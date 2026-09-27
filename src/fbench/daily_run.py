"""The daily run over results/forecasts.csv and results/evaluation.csv:
logs today's forecasts, scores the rows whose hours have passed, and
builds results/LIVE.md, the published record of how each model is doing
on hours none of them saw at fit time. Logged forecast rows are pre-outcome evidence, so nothing here ever
rewrites one."""
import numpy as np
import pandas as pd
from scipy import stats

from fbench.harness_config import (CALIBRATION_ALPHA, CALIBRATION_PERSISTENCE_DAYS,
                           COV90_TARGET, HORIZON, MIN_CALIBRATION_DAYS,
                           QCOLS, QUANTILES, RESULTS_DIR)
from fbench.commit_timing import LATE_COMMIT_REASONS
from fbench.models.base_forecast_model import REGISTRY
from fbench.quantile_scoring import add_skill, score

FORECAST_LOG = RESULTS_DIR / "forecasts.csv"
EVAL_LOG = RESULTS_DIR / "evaluation.csv"
LOG_COLS = ["origin", "target_time", "horizon", "model"] + QCOLS


def _load(path, cols):
    """Read one of the CSV logs with its origin and target_time columns
    parsed as UTC timestamps, returning an empty frame carrying cols when
    the file does not exist yet, so first-run callers need no special
    case."""
    if not path.exists():
        return pd.DataFrame(columns=cols)
    df = pd.read_csv(path)
    for c in ("origin", "target_time"):
        df[c] = pd.to_datetime(df[c], utc=True)
    return df


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
    for name, cls in sorted(REGISTRY.items()):
        if name in done:
            continue
        train = feats.loc[origin - pd.Timedelta(days=cls.train_days):origin]
        assert train.index.max() <= origin
        m = cls()
        m.fit(train)
        q = m.predict(future)
        q = q.assign(origin=origin, model=name,
                     horizon=range(1, HORIZON + 1))
        added.append(q.rename_axis("target_time").reset_index())
    if added:
        RESULTS_DIR.mkdir(exist_ok=True)
        _append(FORECAST_LOG, pd.concat(added, ignore_index=True)[LOG_COLS])
    return sum(len(a) for a in added)


def _append(path, rows):
    """Append rows to one of the CSV logs, writing the header only when
    the file does not exist yet and matching the line terminator the file
    already uses, so nothing already on disk is touched."""
    new = not path.exists()
    term = "\n"
    if not new:
        with open(path, "rb") as f:
            term = "\r\n" if b"\r\n" in f.readline() else "\n"
    rows.to_csv(path, index=False, mode="a", header=new, lineterminator=term)


def score_due(hourly, now=None):
    """Resolve forecast rows whose target hour has ended and has an
    actual, and which are not yet in the evaluation log. Returns rows
    resolved. `now` defaults to the current UTC time and exists so tests
    can place the clock."""
    now = pd.Timestamp.now(tz="UTC") if now is None else now
    fc = _load(FORECAST_LOG, LOG_COLS)
    ev = _load(EVAL_LOG, LOG_COLS + ["y_true"])
    seen = set(zip(ev["origin"], ev["target_time"], ev["model"]))
    pend = fc[~fc.apply(lambda r: (r["origin"], r["target_time"],
                                   r["model"]) in seen, axis=1)].copy()
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


def day_level_scores(ev):
    """Per-model error of the day's average volatility, the level that
    could be one input to a position size, over fully resolved days: the mean absolute
    log error of the median path's 24-hour average against the realized
    24-hour average (day_error), and one minus that error over the
    persistence model's on the same days (day_skill), so a model is
    compared with the baseline only where both forecast the same days."""
    e = ev.dropna(subset=["y_true", "q50"]).copy()
    e["fc"] = np.exp(e["q50"])
    e["rz"] = np.exp(e["y_true"])
    d = e.groupby(["model", "origin"]).agg(n=("target_time", "nunique"),
                                           fc=("fc", "mean"), rz=("rz", "mean"))
    d = d[d["n"] == HORIZON]
    err = np.log(d["rz"] / d["fc"]).abs().unstack("model")
    out = pd.DataFrame({"day_error": err.mean()})
    if "persistence" in err.columns:
        base = err["persistence"]
        skill = {}
        for m in err.columns:
            ok = err[m].notna() & base.notna()
            skill[m] = 1 - err.loc[ok, m].mean() / base[ok].mean()
        out["day_skill"] = pd.Series(skill)
    return out


def matched_skill(ev, model, base="persistence", min_days=MIN_CALIBRATION_DAYS):
    """Skill of model over base on the fully resolved days both forecast,
    with a 95% interval, for two scores: the hourly pinball loss pooled
    over those days, and the day-level error of the 24-hour average (the
    day_error column). Each skill is the mean day-by-day improvement over
    base divided by base's mean, and its interval is the t-interval of
    that mean improvement over the same denominator, which treats each
    day as independent of the last. Returns None below min_days matched
    days or when base is absent."""
    e = ev.dropna(subset=["y_true", *QCOLS]).copy()
    y = e["y_true"].to_numpy()
    loss = sum(np.maximum(a * (y - e[c].to_numpy()), (a - 1) * (y - e[c].to_numpy()))
               for c, a in zip(QCOLS, QUANTILES)) / len(QUANTILES)
    e["pb"], e["fc"], e["rz"] = loss, np.exp(e["q50"]), np.exp(e["y_true"])
    d = e.groupby(["model", "origin"]).agg(n=("target_time", "nunique"),
                                           pb=("pb", "mean"), fc=("fc", "mean"),
                                           rz=("rz", "mean"))
    d = d[d["n"] == HORIZON]
    d["err"] = np.log(d["rz"] / d["fc"]).abs()
    if base not in d.index.get_level_values("model"):
        return None
    both = d.loc[model].join(d.loc[base], lsuffix="_m", rsuffix="_b", how="inner")
    n = len(both)
    if n < min_days:
        return None
    t = float(stats.t.ppf(0.975, n - 1))
    out = {"days": n}
    for key, col in (("hourly", "pb"), ("day", "err")):
        diff = both[f"{col}_b"] - both[f"{col}_m"]
        scale = float(both[f"{col}_b"].mean())
        half = t * float(diff.std(ddof=1)) / np.sqrt(n)
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
    for g in late:
        mins = g["minutes_late"]
        delay = (f"{mins / 60:.0f} hours" if mins >= 60
                 else f"{mins:.0f} minutes")
        why = LATE_COMMIT_REASONS.get(f"{g['origin']:%Y-%m-%d}",
                                      "No reason is recorded for it.")
        lines.append(
            f"- The {g['origin']:%Y-%m-%d} forecast, made from data through "
            f"the hour starting {g['origin']:%H:00} UTC ({g['models']} "
            f"models), was first committed at "
            f"{g['committed']:%Y-%m-%d %H:%M} UTC, {delay} after its first "
            f"target hour completed. {why}")
    return lines + [""]


def _fig_daily(ev, model):
    """Save results/fig_live_daily.png, the day-by-day record of the
    leading model's forecast average against the realized average and
    against the persistence model's own forecast average, and return its
    path. One line per series on one axis, fully resolved days only."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    e = ev.dropna(subset=["y_true", "q50"])

    def _by_day(name):
        """One row per fully resolved day for model name, carrying the
        day's average median forecast and average realized volatility."""
        m = e[e["model"] == name]
        d = m.groupby("origin").agg(n=("target_time", "nunique"),
                                    fc=("q50", lambda s: float(np.exp(s).mean())),
                                    rz=("y_true", lambda s: float(np.exp(s).mean())))
        return d[d["n"] == HORIZON]

    d = _by_day(model)
    base = _by_day("persistence")["fc"].reindex(d.index)
    fig, ax = plt.subplots(figsize=(9, 3))
    ax.plot(d.index, d["rz"], color="#0b0b0b", lw=1.5, marker="o", ms=3,
            label="realized, 24-hour average")
    ax.plot(d.index, d["fc"], color="#2a78d6", lw=1.5, marker="o", ms=3,
            label=f"forecast ({model})")
    ax.plot(d.index, base, color="#eb6834", lw=1.1, ls="--", marker="o",
            ms=2.5, label="persistence forecast")
    ax.set_ylabel("annualized volatility")
    ax.set_ylim(0, float(d["rz"].max()) * 1.3)
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    ax.grid(axis="y", lw=0.5)
    ax.legend(frameon=False, ncol=3, loc="upper left", fontsize=8)
    path = RESULTS_DIR / "fig_live_daily.png"
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return path


def coverage_by_day(ev):
    """Fraction of hours that landed inside each model's 90% band, one
    number per model per scored day. Hourly rows within a day are
    strongly dependent, so the day is the unit the check reasons over."""
    e = ev.dropna(subset=["y_true", "q05", "q95"])
    inside = (e["q05"] <= e["y_true"]) & (e["y_true"] <= e["q95"])
    return inside.groupby([e["model"], e["origin"].dt.date]).mean()


def coverage_test_results(ev):
    """Two-sided t-test of each model's day-level coverage against the
    target, Bonferroni-corrected across the models tested, since testing
    eight at once produces a false rejection often at an uncorrected 5%.

    A model with fewer than MIN_CALIBRATION_DAYS scored days gets no
    result. Neither does one whose daily coverage has no spread at all:
    the test then has no uncertainty to divide by, and inventing one
    would be the same mistake as the fixed floor it replaced."""
    cov = coverage_by_day(ev)
    if cov.empty:
        return {}
    counts = cov.groupby(level=0).size()
    testable = sorted(counts[counts >= MIN_CALIBRATION_DAYS].index)
    if not testable:
        return {}
    alpha = CALIBRATION_ALPHA / len(testable)
    out = {}
    for m in testable:
        d = cov.xs(m, level=0).to_numpy()
        n = len(d)
        se = float(d.std(ddof=1)) / np.sqrt(n)
        if se == 0:
            continue
        mu = float(d.mean())
        t = (mu - COV90_TARGET) / se
        p = float(2 * stats.t.sf(abs(t), n - 1))
        out[m] = {"cov90": mu, "days": n, "t": t, "p": p,
                  "alpha": alpha, "reject": p < alpha}
    return out


def rejection_streaks(ev, cap=CALIBRATION_PERSISTENCE_DAYS):
    """How many consecutive recent scored days the corrected test has
    rejected each model on, counted back from the latest day and stopped
    at cap. Earlier test_results are re-derived from the log rather than
    stored, so the whole check stays reproducible from evaluation.csv
    with no state file to drift out of step with the data."""
    days = sorted(ev["origin"].dt.date.unique())
    streaks = {}
    for k in range(cap):
        if k >= len(days):
            break
        window = ev if k == 0 else ev[ev["origin"].dt.date <= days[-1 - k]]
        rejected = {m for m, v in coverage_test_results(window).items()
                    if v["reject"]}
        if k == 0:
            streaks = {m: 1 for m in rejected}
        else:
            live = [m for m, n in streaks.items() if n == k]
            if not live:
                break
            for m in live:
                if m in rejected:
                    streaks[m] = k + 1
    return streaks


def _figures(model, test_results):
    """Format one model's coverage and p-value as the short phrase the
    calibration sentences splice in, so a flagged model and a pending one
    read the same way."""
    v = test_results[model]
    return f"{model}, coverage {v['cov90']:.4f}, p-value {v['p']:.4f}"


def calibration_lines(ev, days):
    """Calibration result for the live report. Reports a model only
    when the corrected test rejects it on CALIBRATION_PERSISTENCE_DAYS
    consecutive scored days, so a single noisy day cannot raise an alarm
    and a real departure still surfaces within days."""
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

    test_results = coverage_test_results(ev)
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

    streaks = rejection_streaks(ev)
    flagged = {m: n for m, n in streaks.items()
               if n >= CALIBRATION_PERSISTENCE_DAYS}
    if not flagged:
        pending = sorted(streaks)
        if pending:
            parts = "; ".join(
                f"{_figures(m, test_results)}, day {streaks[m]} of "
                f"{CALIBRATION_PERSISTENCE_DAYS}" for m in pending)
            return [f"The calibration check passes and flags no model. It "
                    f"rejects {parts}, short of the "
                    f"{CALIBRATION_PERSISTENCE_DAYS} consecutive days needed "
                    f"to flag it. {method}", ""]
        return [f"The calibration check passes. {method} No model's "
                f"average coverage sits farther from {target} than its "
                f"day-to-day spread would explain.", ""]

    parts = "; ".join(_figures(m, test_results) for m in sorted(flagged))
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
    ev = _load(EVAL_LOG, LOG_COLS + ["y_true"])
    fc = _load(FORECAST_LOG, LOG_COLS)
    lines = ["# Daily record (generated)", ""]
    if ev.empty:
        lines += ["No resolved forecasts yet. First forecasts logged: "
                  f"{fc['origin'].min() if len(fc) else 'none'}."]
    else:
        s = add_skill(score(ev))
        g = s.groupby("model")[["pinball_mean", "mae", "cov50", "cov90",
                                "skill_vs_persistence"]].mean()
        g.insert(0, "days", ev.groupby("model")["origin"]
                 .apply(lambda o: o.dt.date.nunique()))
        g = g.join(day_level_scores(ev))
        days = ev["origin"].dt.date.nunique()
        lines += [
            f"Forecast days scored: {days}. Resolved rows: {len(ev)}. "
            f"Pending (logged, outcome not yet observed): "
            f"{max(0, len(fc) - len(ev))}.",
            "",
            *timing_lines(late),
            g.round(4).sort_values("pinball_mean").to_markdown(), "",
            "The hourly columns score each of the 24 target hours. The day "
            "columns score the day's average volatility, which could be one "
            "input to a position size. day_error is the mean absolute log "
            "error of the 24 hourly median forecasts' average against the "
            "realized average, over fully resolved days, so lower is better. "
            "day_skill is one minus the ratio of that error to the "
            "persistence model's on the same days, so a positive value beats "
            "persistence and 1 would be a perfect forecast.", "",
        ]
        if g["days"].nunique() > 1:
            lines += ["The days column is each model's own count of scored "
                      "days. Models that joined the loop later are averaged "
                      "over fewer days, so the rows above are not "
                      "sample-matched.", ""]
        leader = g["pinball_mean"].idxmin()
        m = matched_skill(ev, leader) if leader != "persistence" else None
        if m:
            (hs, hl, hh), (ds, dl, dh) = m["hourly"], m["day"]
            lines += [
                f"Matched on the {m['days']} fully resolved days that both "
                f"{leader} and persistence forecast, the skill of {leader} "
                f"over persistence is {hs:.2f} on the hourly pinball loss "
                f"(95% interval {hl:.2f} to {hh:.2f}) and {ds:.2f} on the "
                f"day-level error ({dl:.2f} to {dh:.2f}). Pinball loss "
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
        _fig_daily(ev, leader)
        lines += [
            f"The figure below is that day-level record for {leader}, the "
            "current leader: its forecast of each day's average volatility, "
            "the average that realized, and the persistence model's own "
            "forecast of the same average.", "",
            "![day by day: forecast, realized, persistence](fig_live_daily.png)", "",
        ]
        lines += calibration_lines(ev, days)
    path = RESULTS_DIR / "LIVE.md"
    path.write_text("\n".join(lines) + "\n")
    return path
