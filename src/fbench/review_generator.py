"""Yesterday in review: how the most recently resolved forecast day
compared with what realized, followed by the daily forecast's own claims scored
over every resolved day. Generated from the evaluation log and the
hourly realized series, so every number is reproducible from the
committed files."""
import numpy as np
import pandas as pd

from fbench.harness_config import QCOLS, RESULTS_DIR
from fbench.daily_run import EVAL_LOG, _load
from fbench.daily_forecast_generator import LOCAL_TZ, leading_model_asof
from fbench.daily_forecast_scoring import record_lines, score_daily_forecast

# Realized-to-forecast ratio of the day's average. Inside the band the
# day counts as on target; outside, the forecast was too low or too high.
ON_TARGET = (1 / 1.5, 1.5)
LOG_COLS = ["origin", "target_time", "horizon", "model", *QCOLS, "y_true"]


def day_stats(ev):
    """Per-origin severity across every model: mean absolute log error of
    the median and share of truths inside the 90% band."""
    abs_err = (ev["y_true"] - ev["q50"]).abs()
    inside = (ev["q05"] <= ev["y_true"]) & (ev["y_true"] <= ev["q95"])
    return pd.DataFrame({"mae": abs_err.groupby(ev["origin"]).mean(),
                         "cov90": inside.groupby(ev["origin"]).mean()})


def build_review(hourly=None):
    """Return the Markdown body of the review, comparing the most recent
    fully resolved forecast day against what realized and ranking that
    day's error among every scored day. The reported model is the one
    the daily forecast reported on that day, re-derived from the scores
    available then rather than taken from today's results table. Given the
    hourly realized series, the review closes with the daily forecast's own
    claims scored over every resolved day; without it that section is
    omitted."""
    ev = _load(EVAL_LOG, LOG_COLS)
    if ev.empty:
        return "# Yesterday in review (generated)\n\nNo resolved forecasts yet.\n"
    # Only fully resolved days: a partially scored origin would compare
    # the forecast with a fraction of its hours.
    counts = ev.groupby("origin")["target_time"].nunique()
    full = counts[counts == counts.max()].index
    origin = full.max()
    day = ev[ev["origin"] == origin]
    model = leading_model_asof(ev, origin)
    h = day[day["model"] == model].sort_values("target_time").copy()
    for c in QCOLS + ["y_true"]:
        h[c] = np.exp(h[c])  # log RV -> annualized vol

    fc_avg = float(h["q50"].mean())
    rz_avg = float(h["y_true"].mean())
    ratio = rz_avg / fc_avg
    outcome = ("on target" if ON_TARGET[0] <= ratio <= ON_TARGET[1]
               else "too low" if ratio > ON_TARGET[1] else "too high")
    inside = ((h["q05"] <= h["y_true"]) & (h["y_true"] <= h["q95"]))
    above = h["y_true"] > h["q95"]
    below = h["y_true"] < h["q05"]

    stats = day_stats(ev)
    rank = int((stats["mae"] >= stats.loc[origin, "mae"]).sum())
    n_days = len(stats)

    per_model = day.assign(
        err=(day["y_true"] - day["q50"]).abs(),
        inside=(day["q05"] <= day["y_true"]) & (day["y_true"] <= day["q95"]),
        fc=np.exp(day["q50"]),
    ).groupby("model").agg(err=("err", "mean"), cov90=("inside", "mean"),
                           fc=("fc", "mean"))
    best, worst = per_model["err"].idxmin(), per_model["err"].idxmax()
    same_side = (per_model["fc"] < rz_avg).all() or (per_model["fc"] > rz_avg).all()

    local = h["target_time"].dt.tz_convert(LOCAL_TZ)
    miss = (h["y_true"] / h["q50"]).to_numpy()
    worst_ix = np.argsort(-np.abs(np.log(miss)))[:3]
    worst_lines = [
        f"| {local.iloc[i].strftime('%Y-%m-%d %H:00')} | "
        f"{h['q50'].iloc[i]:.0%} | {h['q05'].iloc[i]:.0%}-{h['q95'].iloc[i]:.0%} | "
        f"{h['y_true'].iloc[i]:.0%} | {miss[i]:.1f}x |"
        for i in worst_ix]

    day_local = origin.tz_convert(LOCAL_TZ).date()
    lines = [
        f"# Yesterday in review - forecast issued {day_local} (generated)",
        "",
        f"**The forecast was {outcome}.** The {model} median averaged "
        f"{fc_avg:.0%} annualized volatility over the 24 hours; realized "
        f"averaged {rz_avg:.0%}, {ratio:.2f}x the forecast.",
        "",
        f"- {inside.sum()} of {len(h)} hours landed inside the 90% band "
        f"({above.sum()} above it, {below.sum()} below). A calibrated band "
        f"holds about {round(0.9 * len(h))} of {len(h)}.",
        f"- Across all models this was the "
        f"{'worst' if rank == 1 else _ordinal(rank) + ' worst'} of "
        f"{n_days} scored days (mean log error {stats.loc[origin, 'mae']:.3f}, "
        f"median day {stats['mae'].median():.3f}).",
        f"- Best median that day: {best}; worst: {worst}."
        + (" Every model missed on the same side, so the miss traces to "
           "what was knowable that day rather than to any one model's "
           "choice." if same_side else
           " Models disagreed on the direction of the miss."),
        "",
        "Largest hourly misses (local time, " + LOCAL_TZ + "):",
        "",
        "| hour | forecast median | 90% band | realized | realized/forecast |",
        "|:--|--:|--:|--:|--:|",
        *worst_lines,
        "",
        "Ratios compare annualized volatility levels, not price moves. "
        "This is a volatility review only; it says nothing about price "
        "direction.",
        "",
    ]
    if hourly is not None:
        lines += record_lines(score_daily_forecast(ev, hourly))
    return "\n".join(lines)


def _ordinal(n):
    """Return n with its English ordinal suffix, as in 3 to 3rd, for the
    sentence that ranks the day among all scored days."""
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def write_review(hourly=None):
    """Render the review and save it as results/REVIEW.md, returning that
    path for the daily run to commit. Pass the hourly realized series to
    include the daily forecast's scored claims."""
    path = RESULTS_DIR / "REVIEW.md"
    path.write_text(build_review(hourly))
    return path
