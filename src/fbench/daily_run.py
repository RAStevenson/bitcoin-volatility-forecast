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
    HORIZON,
    MIN_MATCHED_DAYS,
    ORIGIN_HOUR_UTC,
    QCOLS,
    QUANTILES,
    RESULTS_DIR,
)
from fbench.models.base_forecast_model import REGISTRY
from fbench.quantile_scoring import add_skill, score

FORECAST_LOG = RESULTS_DIR / "forecasts.csv"
EVAL_LOG = RESULTS_DIR / "evaluation.csv"
LOG_COLUMNS = ["origin", "target_time", "horizon", "model", *QCOLS]


def _load(path, columns):
    """Read one of the CSV logs with its origin and target_time columns
    parsed as UTC timestamps, returning an empty frame carrying columns
    when the file does not exist yet, so first-run callers need no special
    case."""
    if not path.exists():
        return pd.DataFrame(columns=columns)
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


def log_forecasts(features, origin):
    """Append one 24-hour quantile forecast per registered model, fit on
    data up to origin. Idempotent by (origin, model): rows already logged
    for this origin are skipped, and the file is opened in append mode so
    earlier rows are never rewritten, byte for byte, because the log is
    pre-outcome evidence. Rewriting the whole file used to re-emit every
    old row with float round-trip drift, which made git blame on any row
    point at the latest commit."""
    existing = _load(FORECAST_LOG, LOG_COLUMNS)
    already_logged = set(existing.loc[existing["origin"] == origin, "model"])
    target_times = pd.date_range(origin + pd.Timedelta(hours=1), periods=HORIZON,
                                 freq="h", tz="UTC")
    new_forecasts = []
    for model_name, model_class in sorted(REGISTRY.items()):
        if model_name in already_logged:
            continue
        training_rows = features.loc[
            origin - pd.Timedelta(days=model_class.train_days):origin]
        assert training_rows.index.max() <= origin
        model = model_class()
        model.fit(training_rows)
        quantile_forecast = model.predict(target_times)
        quantile_forecast = quantile_forecast.assign(origin=origin, model=model_name,
                                                     horizon=range(1, HORIZON + 1))
        new_forecasts.append(quantile_forecast.rename_axis("target_time").reset_index())
    if new_forecasts:
        RESULTS_DIR.mkdir(exist_ok=True)
        _append(FORECAST_LOG,
                pd.concat(new_forecasts, ignore_index=True)[LOG_COLUMNS])
    return sum(len(forecast_rows) for forecast_rows in new_forecasts)


def _append(path, rows):
    """Append rows to one of the CSV logs, writing the header only when
    the file does not exist yet and matching the line terminator the file
    already uses, so nothing already on disk is touched."""
    file_is_new = not path.exists()
    line_ending = "\n"
    if not file_is_new:
        with open(path, "rb") as log_file:
            line_ending = "\r\n" if b"\r\n" in log_file.readline() else "\n"
    rows.to_csv(path, index=False, mode="a", header=file_is_new,
                lineterminator=line_ending)


def score_due(hourly, now=None):
    """Resolve forecast rows whose target hour has ended and has an
    actual, and which are not yet in the evaluation log. Returns rows
    resolved. `now` defaults to the current UTC time and exists so tests
    can place the clock."""
    now = pd.Timestamp.now(tz="UTC") if now is None else now
    forecasts = _load(FORECAST_LOG, LOG_COLUMNS)
    evaluations = _load(EVAL_LOG, [*LOG_COLUMNS, "y_true"])
    already_scored = set(zip(evaluations["origin"], evaluations["target_time"],
                             evaluations["model"], strict=True))
    pending = forecasts[~forecasts.apply(
        lambda row: (row["origin"], row["target_time"], row["model"]) in already_scored,
        axis=1)].copy()
    # An hour counts as observed only once it has ended. The realized
    # series marks an hour valid at 45 minutes, so a run late in the hour
    # would otherwise resolve a target on partial data and write that
    # partial truth to the log permanently.
    pending = pending[pending["target_time"] + pd.Timedelta(hours=1) <= now]
    if pending.empty:
        return 0
    pending["y_true"] = hourly["log_rv"].reindex(
        pd.DatetimeIndex(pending["target_time"])).to_numpy()
    resolved = pending.dropna(subset=["y_true"])
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
    scored["forecast_vol"] = np.exp(scored["q50"])
    scored["realized_vol"] = np.exp(scored["y_true"])
    daily = scored.groupby(["model", "origin"]).agg(
        n_hours=("target_time", "nunique"), forecast_vol=("forecast_vol", "mean"),
        realized_vol=("realized_vol", "mean"))
    daily = daily[daily["n_hours"] == HORIZON]
    abs_log_error = (np.log(daily["realized_vol"] / daily["forecast_vol"]).abs()
                     .unstack("model"))
    day_scores = pd.DataFrame({"day_error": abs_log_error.mean()})
    if "persistence" in abs_log_error.columns:
        persistence_error = abs_log_error["persistence"]
        skill = {}
        for model_name in abs_log_error.columns:
            both_scored = abs_log_error[model_name].notna() & persistence_error.notna()
            skill[model_name] = (1 - abs_log_error.loc[both_scored, model_name].mean()
                                 / persistence_error[both_scored].mean())
        day_scores["day_skill"] = pd.Series(skill)
    return day_scores


def matched_skill(evaluations, model, base_model_name="persistence",
                  min_days=MIN_MATCHED_DAYS):
    """Skill of model over base_model_name on the fully resolved days both
    forecast, with a 95% interval, for two scores: the hourly pinball loss
    pooled over those days, and the day-level error of the 24-hour average
    (the day_error column). Each skill is the mean day-by-day improvement
    over the base model divided by the base model's mean, and its interval
    is the t-interval of that mean improvement over the same denominator,
    which treats each day as independent of the last. Returns None below
    min_days matched days or when the base model is absent."""
    scored = evaluations.dropna(subset=["y_true", *QCOLS]).copy()
    log_realized_vol = scored["y_true"].to_numpy()
    pinball_loss = sum(
        np.maximum(quantile * (log_realized_vol - scored[column].to_numpy()),
                   (quantile - 1) * (log_realized_vol - scored[column].to_numpy()))
        for column, quantile in zip(QCOLS, QUANTILES, strict=True)) / len(QUANTILES)
    scored["pinball"] = pinball_loss
    scored["forecast_vol"] = np.exp(scored["q50"])
    scored["realized_vol"] = np.exp(scored["y_true"])
    daily = scored.groupby(["model", "origin"]).agg(
        n_hours=("target_time", "nunique"), pinball=("pinball", "mean"),
        forecast_vol=("forecast_vol", "mean"), realized_vol=("realized_vol", "mean"))
    daily = daily[daily["n_hours"] == HORIZON]
    daily["abs_log_error"] = np.log(daily["realized_vol"] / daily["forecast_vol"]).abs()
    if base_model_name not in daily.index.get_level_values("model"):
        return None
    model_and_base_by_day = daily.loc[model].join(
        daily.loc[base_model_name], lsuffix="_model", rsuffix="_base", how="inner")
    n_days = len(model_and_base_by_day)
    if n_days < min_days:
        return None
    t_critical = float(stats.t.ppf(0.975, n_days - 1))
    skill_by_score: dict = {"days": n_days}
    for score_name, column in (("hourly", "pinball"), ("day", "abs_log_error")):
        improvement = (model_and_base_by_day[f"{column}_base"]
                       - model_and_base_by_day[f"{column}_model"])
        base_mean = float(model_and_base_by_day[f"{column}_base"].mean())
        half_width = t_critical * float(improvement.std(ddof=1)) / np.sqrt(n_days)
        mean_improvement = float(improvement.mean())
        skill_by_score[score_name] = (mean_improvement / base_mean,
                                      (mean_improvement - half_width) / base_mean,
                                      (mean_improvement + half_width) / base_mean)
    return skill_by_score


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
        minutes_late = group["minutes_late"]
        delay = (f"{minutes_late / 60:.0f} hours" if minutes_late >= 60
                 else f"{minutes_late:.0f} minutes")
        reason = (" ".join(filter(None, (
                      LATE_COMMIT_REASONS.get(f"{group['origin']:%Y-%m-%d}"),
                      run_note(group.get("subject")))))
                  or "No reason is recorded for it.")
        lines.append(
            f"- The {group['origin']:%Y-%m-%d} forecast, made from data through "
            f"the hour starting {group['origin']:%H:00} UTC ({group['models']} "
            f"models), was first committed at "
            f"{group['committed']:%Y-%m-%d %H:%M} UTC, {delay} after its first "
            f"target hour completed. {reason}")
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

    def _by_day(model_name):
        """One row per fully resolved day for model_name, carrying the
        day's average median forecast and average realized volatility."""
        model_rows = scored[scored["model"] == model_name]
        daily = model_rows.groupby("origin").agg(
            n_hours=("target_time", "nunique"),
            forecast_vol=("q50", lambda log_values: float(np.exp(log_values).mean())),
            realized_vol=("y_true", lambda log_values: float(np.exp(log_values).mean())))
        return daily[daily["n_hours"] == HORIZON]

    daily = _by_day(model)
    persistence_forecast = _by_day("persistence")["forecast_vol"].reindex(daily.index)
    fig, ax = plt.subplots(figsize=(9, 3))
    ax.plot(daily.index, daily["realized_vol"], color="#0b0b0b", lw=1.5, marker="o",
            ms=3, label="realized, 24-hour average")
    ax.plot(daily.index, daily["forecast_vol"], color="#2a78d6", lw=1.5, marker="o",
            ms=3, label=f"forecast ({model})")
    ax.plot(daily.index, persistence_forecast, color="#eb6834", lw=1.1, ls="--",
            marker="o", ms=2.5, label="persistence forecast")
    ax.set_ylabel("annualized volatility")
    ax.set_ylim(0, float(daily["realized_vol"].max()) * 1.3)
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    ax.grid(axis="y", lw=0.5)
    ax.legend(frameon=False, ncol=3, loc="upper left", fontsize=8)
    fig.autofmt_xdate()  # dated ticks angled so they cannot overlap
    path = RESULTS_DIR / "figures" / "fig_live_daily.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return path


def write_live_report(late=None):
    """Write results/LIVE.md from the forecast and evaluation logs and
    return its path. The reader gets each model's mean scores against its
    own count of scored days, how many logged rows are still waiting on an
    outcome, and the leader's matched-day skill with its interval. late
    is the timing audit's result, passed by the daily run; see
    timing_lines."""
    evaluations = _load(EVAL_LOG, [*LOG_COLUMNS, "y_true"])
    forecasts = _load(FORECAST_LOG, LOG_COLUMNS)
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
            "The hourly columns score each of the 24 target hours. cov50 "
            "and cov90 are the shares of hours that landed inside a model's "
            "50% and 90% bands, so for well-sized bands they sit near 0.50 "
            "and 0.90. The day "
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
    path = RESULTS_DIR / "LIVE.md"
    path.write_text("\n".join(lines) + "\n")
    return path
