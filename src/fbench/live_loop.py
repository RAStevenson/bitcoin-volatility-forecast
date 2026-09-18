"""Runs the live forecast loop over results/forecasts.csv and
results/evaluation.csv, and builds results/LIVE.md, the published
scoreboard of how each model is doing on hours none of them saw at fit
time. Logged forecast rows are pre-outcome evidence, so nothing here ever
rewrites one."""
import numpy as np
import pandas as pd
from scipy import stats

from fbench.harness_config import (CALIBRATION_ALPHA, CALIBRATION_PERSISTENCE_DAYS,
                           COV90_TARGET, HORIZON, MIN_CALIBRATION_DAYS,
                           QCOLS, RESULTS_DIR)
from fbench.models.forecast_model import REGISTRY
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
        if name.startswith("_") or name in done:
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


def coverage_verdicts(ev):
    """Two-sided t-test of each model's day-level coverage against the
    target, Bonferroni-corrected across the models tested, since testing
    eight at once produces a false rejection often at an uncorrected 5%.

    A model with fewer than MIN_CALIBRATION_DAYS scored days gets no
    verdict. Neither does one whose daily coverage has no spread at all:
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
    at cap. Earlier verdicts are re-derived from the log rather than
    stored, so the whole check stays reproducible from evaluation.csv
    with no state file to drift out of step with the data."""
    days = sorted(ev["origin"].dt.date.unique())
    streaks = {}
    for k in range(cap):
        if k >= len(days):
            break
        window = ev if k == 0 else ev[ev["origin"].dt.date <= days[-1 - k]]
        rejected = {m for m, v in coverage_verdicts(window).items()
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


def _figures(model, verdicts):
    """Format one model's coverage and p-value as the short phrase the
    calibration sentences splice in, so a flagged model and a pending one
    read the same way."""
    v = verdicts[model]
    return f"{model} cov90 {v['cov90']:.4f}, p {v['p']:.4f}"


def calibration_lines(ev, days):
    """Calibration verdict for the live report. Reports a model only
    when the corrected test rejects it on CALIBRATION_PERSISTENCE_DAYS
    consecutive scored days, so a single noisy day cannot raise an alarm
    and a real departure still surfaces within days."""
    need = MIN_CALIBRATION_DAYS + CALIBRATION_PERSISTENCE_DAYS - 1
    if days < need:
        return [f"The calibration check stays inactive until {need} scored "
                f"days ({days} so far), the point at which it can both "
                f"estimate a model's day-to-day coverage spread over "
                f"{MIN_CALIBRATION_DAYS} days and require that verdict to "
                f"repeat on {CALIBRATION_PERSISTENCE_DAYS} consecutive "
                "days. Coverage columns are provisional; each day "
                "contributes ~24 dependent hourly rows, so the effective "
                "sample is the day count.", ""]

    verdicts = coverage_verdicts(ev)
    if not verdicts:
        return ["The calibration check found no model with enough scored "
                f"days to test ({MIN_CALIBRATION_DAYS} required).", ""]
    alpha = next(iter(verdicts.values()))["alpha"]
    method = (f"The test is two-sided on each model's daily coverage "
              f"against {COV90_TARGET:.2f} over {days} scored days, "
              f"Bonferroni-corrected across the {len(verdicts)} models "
              f"tested (per-model alpha {alpha:.4f}).")

    streaks = rejection_streaks(ev)
    flagged = {m: n for m, n in streaks.items()
               if n >= CALIBRATION_PERSISTENCE_DAYS}
    if not flagged:
        pending = sorted(streaks)
        if pending:
            parts = "; ".join(
                f"{_figures(m, verdicts)}, day {streaks[m]} of "
                f"{CALIBRATION_PERSISTENCE_DAYS}" for m in pending)
            return [f"The calibration check passes, flagging no model. It "
                    f"rejects {parts}, short of the "
                    f"{CALIBRATION_PERSISTENCE_DAYS} consecutive days it "
                    f"reports on. {method}", ""]
        return [f"The calibration check passes, with no model's day-level "
                f"90% coverage separable from {COV90_TARGET:.2f} by more "
                f"than sampling noise. {method}", ""]

    parts = "; ".join(_figures(m, verdicts) for m in sorted(flagged))
    return [f"The calibration check flags day-level 90% coverage away from "
            f"{COV90_TARGET:.2f} on {CALIBRATION_PERSISTENCE_DAYS} "
            f"consecutive scored days: {parts}. {method} Bands are left as "
            "each model produces them, and the coverage column is the "
            "honest record of that.", ""]


def write_live_report():
    """Write results/LIVE.md from the forecast and evaluation logs and
    return its path. The reader gets each model's mean scores against its
    own count of scored days, how many logged rows are still waiting on an
    outcome, and the calibration verdict."""
    ev = _load(EVAL_LOG, LOG_COLS + ["y_true"])
    fc = _load(FORECAST_LOG, LOG_COLS)
    lines = ["# Live scoreboard (generated)", ""]
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
            "Every row here was committed to git before its target hour "
            "completed. The commit history is the timestamp evidence.",
            "",
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
        leader = g["pinball_mean"].idxmin()
        _fig_daily(ev, leader)
        lines += [
            f"The figure below is that day-level record for {leader}, the "
            "current leader: its forecast of each day's average volatility, "
            "the average that realized, and the persistence model's own "
            "forecast of the same average.", "",
            "![day by day: forecast, realized, yesterday](fig_live_daily.png)", "",
        ]
        if g["days"].nunique() > 1:
            lines += ["The days column is each model's own count of scored "
                      "days. Models that joined the loop later are averaged "
                      "over fewer days, so the rows above are not "
                      "sample-matched.", ""]
        lines += calibration_lines(ev, days)
    path = RESULTS_DIR / "LIVE.md"
    path.write_text("\n".join(lines) + "\n")
    return path
