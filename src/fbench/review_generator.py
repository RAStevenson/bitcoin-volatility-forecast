"""Yesterday in review: how the most recently resolved forecast day
compared with what realized, followed by the daily forecast's own claims scored
over every resolved day. Generated from the evaluation log and the
hourly realized series, so every number is reproducible from the
committed files."""
import math

import numpy as np
import pandas as pd

from fbench.daily_forecast_generator import LOCAL_TZ, leading_model_asof, ordinal
from fbench.daily_forecast_scoring import record_lines, score_daily_forecast
from fbench.daily_run import EVAL_LOG, _load
from fbench.harness_config import QCOLS, RESULTS_DIR

# Realized-to-forecast ratio of the day's average. Inside the band the
# day counts as on target; outside, the forecast was too low or too high.
ON_TARGET = (1 / 1.5, 1.5)
EVAL_LOG_COLUMNS = ["origin", "target_time", "horizon", "model", *QCOLS, "y_true"]


def day_stats(evaluations):
    """Per-origin severity across every model: mean absolute log error of
    the median and share of truths inside the 90% band."""
    abs_log_error = (evaluations["y_true"] - evaluations["q50"]).abs()
    inside_band = ((evaluations["q05"] <= evaluations["y_true"])
                   & (evaluations["y_true"] <= evaluations["q95"]))
    return pd.DataFrame({"mae": abs_log_error.groupby(evaluations["origin"]).mean(),
                         "cov90": inside_band.groupby(evaluations["origin"]).mean()})


def build_review(hourly=None):
    """Return the Markdown body of the review, comparing the most recent
    fully resolved forecast day against what realized and ranking that
    day's error among every scored day. The reported model is the one
    the daily forecast reported on that day, re-derived from the scores
    available then rather than taken from today's results table. Given the
    hourly realized series, the review closes with the daily forecast's own
    claims scored over every resolved day; without it that section is
    omitted."""
    evaluations = _load(EVAL_LOG, EVAL_LOG_COLUMNS)
    if evaluations.empty:
        return "# Yesterday in review (generated)\n\nNo resolved forecasts yet.\n"
    # Only fully resolved days: a partially scored origin would compare
    # the forecast with a fraction of its hours.
    target_hours_per_origin = evaluations.groupby("origin")["target_time"].nunique()
    full_origins = target_hours_per_origin[
        target_hours_per_origin == target_hours_per_origin.max()].index
    origin = full_origins.max()
    day_evaluations = evaluations[evaluations["origin"] == origin]
    model = leading_model_asof(evaluations, origin)
    model_hours = (day_evaluations[day_evaluations["model"] == model]
                   .sort_values("target_time").copy())
    for column in [*QCOLS, "y_true"]:
        model_hours[column] = np.exp(model_hours[column])  # log RV -> annualized vol

    forecast_average = float(model_hours["q50"].mean())
    realized_average = float(model_hours["y_true"].mean())
    ratio = realized_average / forecast_average
    outcome = ("on target" if ON_TARGET[0] <= ratio <= ON_TARGET[1]
               else "too low" if ratio > ON_TARGET[1] else "too high")
    inside_band = ((model_hours["q05"] <= model_hours["y_true"])
                   & (model_hours["y_true"] <= model_hours["q95"]))
    above_band = model_hours["y_true"] > model_hours["q95"]
    below_band = model_hours["y_true"] < model_hours["q05"]

    scores_by_day = day_stats(evaluations)
    day_abs_log_error = scores_by_day.loc[origin, "mae"]
    n_days = len(scores_by_day)
    rank_text = _rank_phrase(
        int((scores_by_day["mae"] > day_abs_log_error).sum()) + 1,
        int((scores_by_day["mae"] < day_abs_log_error).sum()) + 1, n_days)

    per_model = day_evaluations.assign(
        abs_log_error=(day_evaluations["y_true"] - day_evaluations["q50"]).abs(),
        inside_band=((day_evaluations["q05"] <= day_evaluations["y_true"])
                     & (day_evaluations["y_true"] <= day_evaluations["q95"])),
        forecast_vol=np.exp(day_evaluations["q50"]),
    ).groupby("model").agg(abs_log_error=("abs_log_error", "mean"),
                           cov90=("inside_band", "mean"),
                           forecast_vol=("forecast_vol", "mean"))
    best = per_model["abs_log_error"].idxmin()
    worst = per_model["abs_log_error"].idxmax()
    shared_direction = (
        "too low" if (per_model["forecast_vol"] < realized_average).all()
        else "too high" if (per_model["forecast_vol"] > realized_average).all()
        else None)

    local_times = model_hours["target_time"].dt.tz_convert(LOCAL_TZ)
    realized_to_forecast = (model_hours["y_true"] / model_hours["q50"]).to_numpy()
    worst_hour_positions = np.argsort(-np.abs(np.log(realized_to_forecast)))[:3]
    worst_lines = [
        f"| {local_times.iloc[i].strftime('%Y-%m-%d %H:00')} | "
        f"{model_hours['q50'].iloc[i]:.0%} | "
        f"{model_hours['q05'].iloc[i]:.0%}-{model_hours['q95'].iloc[i]:.0%} | "
        f"{model_hours['y_true'].iloc[i]:.0%} | {realized_to_forecast[i]:.1f}x |"
        for i in worst_hour_positions]

    issue_date = origin.tz_convert(LOCAL_TZ).date()
    n_hours = len(model_hours)
    lines = [
        f"# Yesterday in review - forecast issued {issue_date} (generated)",
        "",
        f"**The forecast was {outcome}.** The {model} median averaged "
        f"{forecast_average:.0%} annualized volatility over the 24 hours; realized "
        f"averaged {realized_average:.0%}, {ratio:.2f}x the forecast. The "
        f"forecast counts as on target when the realized volatility averages "
        f"within a factor of {ON_TARGET[1]:g} of the forecast, above or below it.",
        "",
        f"- {inside_band.sum()} of {n_hours} hours landed inside the 90% band "
        f"({above_band.sum()} above it, {below_band.sum()} below). A calibrated band "
        f"holds about {round(0.9 * n_hours)} of {n_hours}.",
        f"- Across all models the day's mean absolute log error was "
        f"{day_abs_log_error:.3f}, {rank_text} (median day "
        f"{scores_by_day['mae'].median():.3f}).",
        f"- Among the models, {best} had the smallest mean absolute log "
        f"error that day and {worst} the largest."
        + (f" Every model forecast {shared_direction}, so the error traces to what "
           "was knowable that day rather than to any one model's choice."
           if shared_direction else
           " Some models forecast too high and others too low."),
        "",
        "Largest hourly errors (local time, " + LOCAL_TZ + "):",
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
        lines += record_lines(score_daily_forecast(evaluations, hourly))
    return "\n".join(lines)


def _rank_phrase(from_worst, from_best, n_days):
    """The day's error placed among the scored days. A day more than
    ceil(n_days / 3) places from either end is said to be in the middle
    third, since an exact place such as "the 28th largest" reads as a
    judgment on a day near the median. A day outside it is counted from
    the nearer end, so the lowest-error day on record reads as "the
    smallest of 57 scored days" rather than "the 57th largest". from_worst
    is one more than the count of days with a larger error, so 1 is the
    largest, and from_best one more than the count with a smaller error,
    so 1 is the smallest; days tied on error share a place, and a day
    equally far from both ends is at the median. A lone day has nothing
    to rank against."""
    if n_days == 1:
        return "with no other scored day to rank it against"
    nearer = min(from_worst, from_best)
    if nearer > math.ceil(n_days / 3):
        return f"in the middle third of {n_days} scored days"
    if from_worst == from_best:
        return f"at the median of {n_days} scored days"
    end = "smallest" if from_best < from_worst else "largest"
    rank = end if nearer == 1 else f"{ordinal(nearer)} {end}"
    return f"the {rank} of {n_days} scored days"


def write_review(hourly=None):
    """Render the review and save it as results/REVIEW.md, returning that
    path for the daily run to commit. Pass the hourly realized series to
    include the daily forecast's scored claims."""
    path = RESULTS_DIR / "REVIEW.md"
    path.write_text(build_review(hourly))
    return path
