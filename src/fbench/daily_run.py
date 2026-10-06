"""The daily run over results/forecasts.csv and results/evaluation.csv:
logs today's forecasts, scores the rows whose hours have passed, and
builds results/LIVE.md, the published record of how each model is doing
on hours none of them saw at fit time. Logged forecast rows are
pre-outcome evidence, so nothing here ever rewrites one."""
import numpy as np
import pandas as pd
from scipy import stats

from fbench.commit_timing import LATE_COMMIT_REASONS, run_note
from fbench.harness_config import (
    CALIBRATION_ALPHA,
    CALIBRATION_PERSISTENCE_DAYS,
    COV90_TARGET,
    HORIZON,
    MIN_CALIBRATION_DAYS,
    ORIGIN_HOUR_UTC,
    QCOLS,
    QUANTILES,
    RESULTS_DIR,
)
from fbench.models.base_forecast_model import REGISTRY
from fbench.quantile_scoring import add_skill, score

FORECAST_LOG = RESULTS_DIR / "forecasts.csv"
EVAL_LOG = RESULTS_DIR / "evaluation.csv"
LOG_COLS = ["origin", "target_time", "horizon", "model", *QCOLS]


def _load(path, cols):
    """Read one of the CSV logs with its origin and target_time columns
    parsed as UTC timestamps, returning an empty frame carrying cols when
    the file does not exist yet, so first-run callers need no special
    case."""
    if not path.exists():
        return pd.DataFrame(columns=cols)
    log = pd.read_csv(path)
    for column in ("origin", "target_time"):
        log[column] = pd.to_datetime(log[column], utc=True)
    return log


def fixed_origin(hourly, now=None):
    """The forecast origin for a run at now: today's ORIGIN_HOUR_UTC
    hour, which must have completed, the same clock hour every day. A
    run that starts hours late therefore forecasts the window an on-time
    run would have and sees no data past it, which keeps every day of
    the record on one window. Raises if that hour has not closed yet,
    because yesterday's forecast is already logged and the run would
    still commit the extended series and scoring under today's date,
    which the workflow's skip guard reads as the day's run, so the
    on-time run would be skipped and today's forecast never logged.
    Raises if the series has no
    realized value at that hour, because forecasting from a substitute
    origin would put that day on a different window, and a visible
    failure is what the record should show."""
    now = pd.Timestamp.now(tz="UTC") if now is None else now
    origin = now.floor("D") + pd.Timedelta(hours=ORIGIN_HOUR_UTC)
    if origin + pd.Timedelta(hours=1) > now:
        raise ValueError(f"the origin hour {origin:%H:%M} UTC has not closed "
                         f"yet; run after {origin + pd.Timedelta(hours=1):%H:%M} UTC")
    if origin not in hourly.index or pd.isna(hourly.loc[origin, "log_rv"]):
        raise ValueError(f"no realized value at the origin hour {origin}")
    return origin


def log_forecasts(feats, origin):
    """Append one 24-hour quantile forecast per registered model, fit on
    data up to origin. Idempotent by (origin, model): rows already logged
    for this origin are skipped, and the file is opened in append mode so
    earlier rows are never rewritten, byte for byte, because the log is
    pre-outcome evidence. Rewriting the whole file used to re-emit every
    old row with float round-trip drift, which made git blame on any row
    point at the latest commit."""
    existing = _load(FORECAST_LOG, LOG_COLS)
    done = set(existing.loc[existing["origin"] == origin, "model"])
    future = pd.date_range(origin + pd.Timedelta(hours=1), periods=HORIZON,
                           freq="h", tz="UTC")
    added = []
    for model_name, model_class in sorted(REGISTRY.items()):
        if model_name in done:
            continue
        train = feats.loc[origin - pd.Timedelta(days=model_class.train_days):origin]
        assert train.index.max() <= origin
        model = model_class()
        model.fit(train)
        quantile_forecast = model.predict(future)
        quantile_forecast = quantile_forecast.assign(origin=origin, model=model_name,
                                                     horizon=range(1, HORIZON + 1))
        added.append(quantile_forecast.rename_axis("target_time").reset_index())
    if added:
        RESULTS_DIR.mkdir(exist_ok=True)
        _append(FORECAST_LOG, pd.concat(added, ignore_index=True)[LOG_COLS])
    return sum(len(forecast_rows) for forecast_rows in added)


def _append(path, rows):
    """Append rows to one of the CSV logs, writing the header only when
    the file does not exist yet and matching the line terminator the file
    already uses, so nothing already on disk is touched."""
    new = not path.exists()
    term = "\n"
    if not new:
        with open(path, "rb") as log_file:
            term = "\r\n" if b"\r\n" in log_file.readline() else "\n"
    rows.to_csv(path, index=False, mode="a", header=new, lineterminator=term)


def score_due(hourly, now=None):
    """Resolve forecast rows whose target hour has ended and has an
    actual, and which are not yet in the evaluation log. Returns rows
    resolved. `now` defaults to the current UTC time and exists so tests
    can place the clock."""
    now = pd.Timestamp.now(tz="UTC") if now is None else now
    forecasts = _load(FORECAST_LOG, LOG_COLS)
    evaluations = _load(EVAL_LOG, [*LOG_COLS, "y_true"])
    seen = set(zip(evaluations["origin"], evaluations["target_time"],
                   evaluations["model"], strict=True))
    pend = forecasts[~forecasts.apply(lambda row: (row["origin"], row["target_time"],
                                                   row["model"]) in seen, axis=1)].copy()
    # An hour counts as observed only once it has ended. The realized
    # series marks an hour valid at 45 minutes, so a run late in the hour
    # would otherwise resolve a target on partial data and write that
    # partial truth to the log permanently.
    pend = pend[pend["target_time"] + pd.Timedelta(hours=1) <= now]
    if pend.empty:
        return 0
    pend["y_true"] = hourly["log_rv"].reindex(
        pd.DatetimeIndex(pend["target_time"])).to_numpy()
    resolved = pend.dropna(subset=["y_true"])
    if resolved.empty:
        return 0
    _append(EVAL_LOG, resolved)
    return len(resolved)


def day_level_scores(evaluations):
    """Per-model error of the day's average volatility, the level that
    could be one input to a position size, over fully resolved days: the mean absolute
    log error of the median path's 24-hour average against the realized
    24-hour average (day_error), and one minus that error over the
    persistence model's on the same days (day_skill), so a model is
    compared with the baseline only where both forecast the same days."""
    scored = evaluations.dropna(subset=["y_true", "q50"]).copy()
    scored["fc"] = np.exp(scored["q50"])
    scored["rz"] = np.exp(scored["y_true"])
    daily = scored.groupby(["model", "origin"]).agg(n=("target_time", "nunique"),
                                                    fc=("fc", "mean"), rz=("rz", "mean"))
    daily = daily[daily["n"] == HORIZON]
    err = np.log(daily["rz"] / daily["fc"]).abs().unstack("model")
    out = pd.DataFrame({"day_error": err.mean()})
    if "persistence" in err.columns:
        base = err["persistence"]
        skill = {}
        for model_name in err.columns:
            both_scored = err[model_name].notna() & base.notna()
            skill[model_name] = (1 - err.loc[both_scored, model_name].mean()
                                 / base[both_scored].mean())
        out["day_skill"] = pd.Series(skill)
    return out


def matched_skill(evaluations, model, base="persistence", min_days=MIN_CALIBRATION_DAYS):
    """Skill of model over base on the fully resolved days both forecast,
    with a 95% interval, for two scores: the hourly pinball loss pooled
    over those days, and the day-level error of the 24-hour average (the
    day_error column). Each skill is the mean day-by-day improvement over
    base divided by base's mean, and its interval is the t-interval of
    that mean improvement over the same denominator, which treats each
    day as independent of the last. Returns None below min_days matched
    days or when base is absent."""
    scored = evaluations.dropna(subset=["y_true", *QCOLS]).copy()
    log_realized_vol = scored["y_true"].to_numpy()
    loss = sum(np.maximum(quantile * (log_realized_vol - scored[column].to_numpy()),
                          (quantile - 1) * (log_realized_vol - scored[column].to_numpy()))
               for column, quantile in zip(QCOLS, QUANTILES, strict=True)) / len(QUANTILES)
    scored["pb"], scored["fc"], scored["rz"] = (loss, np.exp(scored["q50"]),
                                                np.exp(scored["y_true"]))
    daily = scored.groupby(["model", "origin"]).agg(n=("target_time", "nunique"),
                                                    pb=("pb", "mean"), fc=("fc", "mean"),
                                                    rz=("rz", "mean"))
    daily = daily[daily["n"] == HORIZON]
    daily["err"] = np.log(daily["rz"] / daily["fc"]).abs()
    if base not in daily.index.get_level_values("model"):
        return None
    both = daily.loc[model].join(daily.loc[base], lsuffix="_m", rsuffix="_b", how="inner")
    n_days = len(both)
    if n_days < min_days:
        return None
    t_critical = float(stats.t.ppf(0.975, n_days - 1))
    out: dict = {"days": n_days}
    for key, col in (("hourly", "pb"), ("day", "err")):
        diff = both[f"{col}_b"] - both[f"{col}_m"]
        scale = float(both[f"{col}_b"].mean())
        half = t_critical * float(diff.std(ddof=1)) / np.sqrt(n_days)
        mid = float(diff.mean())
        out[key] = ((mid) / scale, (mid - half) / scale, (mid + half) / scale)
    return out


def timing_lines(late):
    """LIVE.md's statement about when its rows were committed. late
    is the list from commit_timing.late_groups, empty when the audit found
    nothing, or None when no audit ran, in which case the claim is left to
    scripts/run_verify_timing.py rather than asserted."""
    if late is None:
        return ["The commit history is the timestamp evidence for every row "
                "here, and scripts/run_verify_timing.py audits it.", ""]
    audit = ("Each run audits every earlier commit of the forecast log, so "
             "a day's rows are checked on the run after the one that "
             "committed them. The commit history is the timestamp evidence.")
    claim = ("Every row from an earlier run was committed to git before its "
             "target hour completed")
    if not late:
        return [f"{claim}, with no exceptions so far. {audit}", ""]
    lines = [f"{claim}. Any exceptions and their reasons are listed below. "
             f"{audit}", ""]
    for group in late:
        mins = group["minutes_late"]
        delay = (f"{mins / 60:.0f} hours" if mins >= 60
                 else f"{mins:.0f} minutes")
        why = (LATE_COMMIT_REASONS.get(f"{group['origin']:%Y-%m-%d}")
               or run_note(group.get("subject"))
               or "No reason is recorded for it.")
        lines.append(
            f"- The {group['origin']:%Y-%m-%d} forecast, made from data through "
            f"the hour starting {group['origin']:%H:00} UTC ({group['models']} "
            f"models), was first committed at "
            f"{group['committed']:%Y-%m-%d %H:%M} UTC, {delay} after its first "
            f"target hour completed. {why}")
    return [*lines, ""]


def _fig_daily(evaluations, model):
    """Save results/figures/fig_live_daily.png, the day-by-day record of the
    leading model's forecast average against the realized average and
    against the persistence model's own forecast average, and return its
    path. One line per series on one axis, fully resolved days only."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker

    scored = evaluations.dropna(subset=["y_true", "q50"])

    def _by_day(name):
        """One row per fully resolved day for model name, carrying the
        day's average median forecast and average realized volatility."""
        model_rows = scored[scored["model"] == name]
        daily = model_rows.groupby("origin").agg(
            n=("target_time", "nunique"),
            fc=("q50", lambda log_values: float(np.exp(log_values).mean())),
            rz=("y_true", lambda log_values: float(np.exp(log_values).mean())))
        return daily[daily["n"] == HORIZON]

    daily = _by_day(model)
    base = _by_day("persistence")["fc"].reindex(daily.index)
    fig, ax = plt.subplots(figsize=(9, 3))
    ax.plot(daily.index, daily["rz"], color="#0b0b0b", lw=1.5, marker="o", ms=3,
            label="realized, 24-hour average")
    ax.plot(daily.index, daily["fc"], color="#2a78d6", lw=1.5, marker="o", ms=3,
            label=f"forecast ({model})")
    ax.plot(daily.index, base, color="#eb6834", lw=1.1, ls="--", marker="o",
            ms=2.5, label="persistence forecast")
    ax.set_ylabel("annualized volatility")
    ax.set_ylim(0, float(daily["rz"].max()) * 1.3)
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    ax.grid(axis="y", lw=0.5)
    ax.legend(frameon=False, ncol=3, loc="upper left", fontsize=8)
    fig.autofmt_xdate()  # dated ticks angled so they cannot overlap
    path = RESULTS_DIR / "figures" / "fig_live_daily.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return path


def coverage_by_day(evaluations):
    """Fraction of hours that landed inside each model's 90% band, one
    number per model per scored day. Hourly rows within a day are
    strongly dependent, so the day is the unit the check reasons over."""
    scored = evaluations.dropna(subset=["y_true", "q05", "q95"])
    inside = (scored["q05"] <= scored["y_true"]) & (scored["y_true"] <= scored["q95"])
    return inside.groupby([scored["model"], scored["origin"].dt.date]).mean()


def coverage_test_results(evaluations):
    """Two-sided t-test of each model's day-level coverage against the
    target, Bonferroni-corrected across the models tested, since testing
    eight at once produces a false rejection often at an uncorrected 5%.

    A model with fewer than MIN_CALIBRATION_DAYS scored days gets no
    result. Neither does one whose daily coverage has no spread at all:
    the test then has no uncertainty to divide by, and inventing one
    would be the same mistake as the fixed floor it replaced."""
    cov = coverage_by_day(evaluations)
    if cov.empty:
        return {}
    counts = cov.groupby(level=0).size()
    testable = sorted(counts[counts >= MIN_CALIBRATION_DAYS].index)
    if not testable:
        return {}
    alpha = CALIBRATION_ALPHA / len(testable)
    out = {}
    for model_name in testable:
        daily_coverage = cov.xs(model_name, level=0).to_numpy()
        n_days = len(daily_coverage)
        standard_error = float(daily_coverage.std(ddof=1)) / np.sqrt(n_days)
        if standard_error == 0:
            continue
        mean_coverage = float(daily_coverage.mean())
        t_statistic = (mean_coverage - COV90_TARGET) / standard_error
        p_value = float(2 * stats.t.sf(abs(t_statistic), n_days - 1))
        out[model_name] = {"cov90": mean_coverage, "days": n_days, "t": t_statistic,
                           "p": p_value, "alpha": alpha, "reject": p_value < alpha}
    return out


def rejection_streaks(evaluations, cap=CALIBRATION_PERSISTENCE_DAYS):
    """How many consecutive recent scored days the corrected test has
    rejected each model on, counted back from the latest day and stopped
    at cap. Earlier test_results are re-derived from the log rather than
    stored, so the whole check stays reproducible from evaluation.csv
    with no state file to drift out of step with the data."""
    days = sorted(evaluations["origin"].dt.date.unique())
    streaks = {}
    for days_back in range(cap):
        if days_back >= len(days):
            break
        window = (evaluations if days_back == 0 else
                  evaluations[evaluations["origin"].dt.date <= days[-1 - days_back]])
        rejected = {model_name for model_name, result in coverage_test_results(window).items()
                    if result["reject"]}
        if days_back == 0:
            streaks = dict.fromkeys(rejected, 1)
        else:
            live = [model_name for model_name, streak in streaks.items()
                    if streak == days_back]
            if not live:
                break
            for model_name in live:
                if model_name in rejected:
                    streaks[model_name] = days_back + 1
    return streaks


def _figures(model, test_results):
    """Format one model's coverage and p-value as the short phrase the
    calibration sentences splice in, so a flagged model and a pending one
    read the same way."""
    result = test_results[model]
    return f"{model}, coverage {result['cov90']:.4f}, p-value {result['p']:.4f}"


def calibration_lines(evaluations, days):
    """Calibration result for the live report. Flags a model only when
    the corrected test rejects it on CALIBRATION_PERSISTENCE_DAYS
    consecutive scored days, and names a shorter streak as pending, so
    a single noisy day cannot raise an alarm and a real departure still
    surfaces within days."""
    need = MIN_CALIBRATION_DAYS + CALIBRATION_PERSISTENCE_DAYS - 1
    if days < need:
        return [f"The calibration check stays inactive until {need} scored "
                f"days ({days} so far), the point at which it can both "
                f"estimate a model's day-to-day coverage spread over "
                f"{MIN_CALIBRATION_DAYS} days and require that result to "
                f"repeat on {CALIBRATION_PERSISTENCE_DAYS} consecutive "
                "days. Coverage columns are provisional; each day "
                "contributes ~24 dependent hourly rows, so the effective "
                "sample is the day count.", ""]

    test_results = coverage_test_results(evaluations)
    if not test_results:
        return ["The calibration check found no model with enough scored "
                f"days to test ({MIN_CALIBRATION_DAYS} required).", ""]
    alpha = next(iter(test_results.values()))["alpha"]
    n_models = len(test_results)
    target = f"{COV90_TARGET:.2f}"
    method = (
        f"A model's 90% band is meant to contain the realized value on about "
        f"90% of hours. Coverage is the share of hours that landed inside "
        f"it. The check takes that share for each day a model has been "
        f"scored, one number per day. It asks whether the average of those "
        f"numbers sits farther from {target} than their day-to-day spread "
        f"would explain, in either direction (a two-sided t-test). The "
        f"p-value is the chance of an average at least that far from "
        f"{target} if the model's true coverage were exactly {target}. "
        f"Because {n_models} models are tested at once, each is held to a "
        f"threshold of {CALIBRATION_ALPHA:.2f} divided by {n_models}, or "
        f"{alpha:.4f}, so that the chance of a false alarm across all of "
        f"them stays at or below {CALIBRATION_ALPHA:.0%} (a Bonferroni "
        f"correction). A p-value below that threshold is a rejection. A "
        f"model is flagged only after it is rejected on "
        f"{CALIBRATION_PERSISTENCE_DAYS} consecutive scored days, so one "
        f"noisy day cannot raise an alarm.")

    streaks = rejection_streaks(evaluations)
    flagged = {model_name: streak for model_name, streak in streaks.items()
               if streak >= CALIBRATION_PERSISTENCE_DAYS}
    if not flagged:
        pending = sorted(streaks)
        if pending:
            parts = "; ".join(
                f"{_figures(model_name, test_results)}, day {streaks[model_name]} of "
                f"{CALIBRATION_PERSISTENCE_DAYS}" for model_name in pending)
            return [f"The calibration check passes and flags no model. It "
                    f"rejects {parts}, short of the "
                    f"{CALIBRATION_PERSISTENCE_DAYS} consecutive days needed "
                    f"to flag it. {method}", ""]
        return [f"The calibration check passes. {method} No model crossed "
                f"that threshold.", ""]

    parts = "; ".join(_figures(model_name, test_results)
                      for model_name in sorted(flagged))
    return [f"The calibration check flags these models, whose average "
            f"coverage has sat farther from {target} than day-to-day spread "
            f"would explain on {CALIBRATION_PERSISTENCE_DAYS} consecutive "
            f"scored days: {parts}. Bands are left as each model produces "
            f"them, and the coverage column is the record of that. "
            f"{method}", ""]


def write_live_report(late=None):
    """Write results/LIVE.md from the forecast and evaluation logs and
    return its path. The reader gets each model's mean scores against its
    own count of scored days, how many logged rows are still waiting on an
    outcome, the leader's matched-day skill with its interval, and the
    calibration result. late is the timing audit's result, passed by the
    daily run; see timing_lines."""
    evaluations = _load(EVAL_LOG, [*LOG_COLS, "y_true"])
    forecasts = _load(FORECAST_LOG, LOG_COLS)
    lines = ["# Daily record (generated)", ""]
    if evaluations.empty:
        lines += ["No resolved forecasts yet. First forecasts logged: "
                  f"{forecasts['origin'].min() if len(forecasts) else 'none'}."]
    else:
        scores = add_skill(score(evaluations))
        summary = scores.groupby("model")[["pinball_mean", "mae", "cov50", "cov90",
                                           "skill_vs_persistence"]].mean()
        summary.insert(0, "days", evaluations.groupby("model")["origin"]
                       .apply(lambda origins: origins.dt.date.nunique()))
        summary = summary.join(day_level_scores(evaluations))
        days = evaluations["origin"].dt.date.nunique()
        lines += [
            f"Forecast days scored: {days}. Resolved rows: {len(evaluations)}. "
            f"Pending (logged, outcome not yet observed): "
            f"{max(0, len(forecasts) - len(evaluations))}.",
            "",
            *timing_lines(late),
            summary.round(4).sort_values("pinball_mean").to_markdown(), "",
            "The hourly columns score each of the 24 target hours. The day "
            "columns score the day's average volatility, which could be one "
            "input to a position size. day_error is the mean absolute log "
            "error of the 24 hourly median forecasts' average against the "
            "realized average, over fully resolved days, so lower is better. "
            "day_skill is one minus the ratio of that error to the "
            "persistence model's on the same days, so a positive value beats "
            "persistence and 1 would be a perfect forecast.", "",
        ]
        if summary["days"].nunique() > 1:
            lines += ["The days column is each model's own count of scored "
                      "days. Models that joined the loop later are averaged "
                      "over fewer days, so the rows above are not "
                      "sample-matched.", ""]
        leader = summary["pinball_mean"].idxmin()
        matched = matched_skill(evaluations, leader) if leader != "persistence" else None
        if matched:
            hourly_skill, hourly_low, hourly_high = matched["hourly"]
            day_skill, day_low, day_high = matched["day"]
            lines += [
                f"Matched on the {matched['days']} fully resolved days that both "
                f"{leader} and persistence forecast, the skill of {leader} "
                f"over persistence is {hourly_skill:.2f} on the hourly pinball "
                f"loss (95% interval {hourly_low:.2f} to {hourly_high:.2f}) and "
                f"{day_skill:.2f} on the day-level error ({day_low:.2f} to "
                f"{day_high:.2f}). Pinball loss "
                "scores the whole low-to-high forecast band, not just its "
                "middle, and lower is better. The hourly figure pools the "
                "loss over those days, while the table's "
                "skill_vs_persistence averages the 24 per-hour skills, each "
                "model over its own days. Each interval comes from the "
                "day-to-day spread of the gap between the two models' daily "
                "scores and treats each day as independent of the last. An "
                "interval that stays above zero means that, on these days, "
                "the lead over persistence is larger than day-to-day noise "
                "would explain.", ""]
        _fig_daily(evaluations, leader)
        lines += [
            f"The figure below is that day-level record for {leader}, the "
            "current leader: its forecast of each day's average volatility, "
            "the average that realized, and the persistence model's own "
            "forecast of the same average.", "",
            "![day by day: forecast, realized, persistence]"
            "(figures/fig_live_daily.png)", "",
        ]
        lines += calibration_lines(evaluations, days)
    path = RESULTS_DIR / "LIVE.md"
    path.write_text("\n".join(lines) + "\n")
    return path
