"""Builds results/OUTLOOK.md, the plain-language read of the latest
logged 24-hour forecast for someone who does not work in volatility.
Every figure is derived at render time from the forecast log and the
hourly realized series, so the prose cannot drift away from the
numbers."""
import numpy as np
import pandas as pd

from fbench.config import ANNUALIZER, QCOLS, QUANTILES, RESULTS_DIR
from fbench.daily import EVAL_LOG, FORECAST_LOG, _load
from fbench.scoring import score

LOCAL_TZ = "America/Chicago"
FALLBACK_MODEL = "gbm"  # full-backtest winner, used until live scores exist


def prob_above(vol_quantiles, threshold):
    """P(X > threshold) by linear interpolation on the five known CDF
    points, clamped to [0.02, 0.98] beyond the tails. Works per hour on
    marginal quantiles; no independence assumption is ever layered on."""
    cdf = np.interp(threshold, vol_quantiles, QUANTILES,
                    left=0.02, right=0.98)
    return float(1.0 - cdf)


def _headline_model():
    """Pick the model that narrates the outlook and return it with the
    short phrase explaining the choice, which is the live pinball leader
    once three origins have been scored and FALLBACK_MODEL before that."""
    # Three origins is a deliberately lower bar than the 10-day
    # calibration gate: picking which model narrates the outlook only
    # needs a best guess, while the calibration line is a published
    # verdict, so that one waits for the larger sample.
    ev = _load(EVAL_LOG, ["origin", "target_time", "horizon", "model",
                          *QCOLS, "y_true"])
    if ev["origin"].nunique() >= 3:
        live = score(ev).groupby("model")["pinball_mean"].mean()
        return live.idxmin(), "the model currently leading the live scoreboard"
    return FALLBACK_MODEL, "the backtest winner while the live sample is young"


def build_outlook(hourly, last_price=None):
    """Return the Markdown body of the outlook, turning the headline
    model's latest 24-hour quantiles into typical hourly and daily move
    sizes, a regime word set against the past year, and the loud and calm
    hours ahead. Without last_price the moves are quoted in percent only,
    since a dollar figure has no price to hang on."""
    fc = _load(FORECAST_LOG, ["origin", "target_time", "horizon", "model",
                              *QCOLS])
    if fc.empty:
        return "# Volatility outlook\n\nNo forecasts logged yet.\n"
    model, model_why = _headline_model()
    origin = fc["origin"].max()
    today = fc[(fc["origin"] == origin) & (fc["model"] == model)].copy()
    today = today.sort_values("target_time")
    vol = np.exp(today[QCOLS].to_numpy())  # log RV -> annualized vol

    rv = hourly["rv"].dropna()
    year = rv.loc[rv.index >= rv.index.max() - pd.Timedelta(days=365)]
    daily_avg = year.rolling(24).mean().dropna()

    med_path = vol[:, 2]
    fc_avg = float(med_path.mean())
    # Human translation: annualized vol / sqrt(hours per year) is the
    # typical single-hour move. The daily figure is the root of summed
    # hourly variances, a one-sigma close-to-close move rather than a
    # range; averaging the hourly sigmas first would understate it
    # whenever vol varies across the day.
    hr_move = fc_avg / ANNUALIZER
    day_move = float(np.sqrt(np.sum((med_path / ANNUALIZER) ** 2)))
    pct = float((daily_avg < fc_avg).mean() * 100)
    hi_thresh = float(year.quantile(0.90))
    # The quiet/normal boundary compares fc_avg to the distribution of
    # rolling 24h averages, so the printed threshold must come from the
    # same distribution or it is not the deciding line.
    q_thresh = float(daily_avg.quantile(0.30))

    regime = ("quiet" if pct < 30 else
              "normal" if pct < 70 else
              "elevated" if pct < 90 else "high")
    last24 = float(rv.iloc[-24:].mean())
    ratio = fc_avg / last24
    trend = ("rising" if ratio > 1.10 else
             "falling" if ratio < 0.90 else "steady")

    p_high = [prob_above(vol[i], hi_thresh) for i in range(len(vol))]
    exp_high_hours = float(np.sum(p_high))
    likely_high = int(np.sum(np.array(p_high) > 0.5))
    # prob_above clamps at 0.02 beyond the fitted quantiles, so when every
    # hour sits at the clamp the sum is a floor (24 x 0.02), not a
    # forecast, and printing it as one would dress a constant as
    # information.
    all_at_floor = all(p <= 0.02 + 1e-9 for p in p_high)
    hi_move = hi_thresh / ANNUALIZER
    if all_at_floor:
        high_line = (f"- No hour shows a meaningful chance of running "
                     f"high, above {hi_thresh:.0%} annualized (an hourly "
                     f"move over {hi_move:.2%}), higher than 90% of "
                     f"individual hours in the past year; every forecast "
                     f"band sits well below that line.")
    else:
        high_line = (f"- The next 24 hours are expected to include about "
                     f"{exp_high_hours:.1f} hours running high, above "
                     f"{hi_thresh:.0%} annualized (an hourly move over "
                     f"{hi_move:.2%}), higher than 90% of individual "
                     f"hours in the past year"
                     + (f"; {likely_high} hours are more likely than not "
                        f"to qualify." if likely_high else "."))

    local = today["target_time"].dt.tz_convert(LOCAL_TZ)
    order = np.argsort(med_path)
    loud = sorted(local.iloc[order[-3:]].dt.strftime("%H:00"))
    calm = sorted(local.iloc[order[:3]].dt.strftime("%H:00"))

    day = origin.tz_convert(LOCAL_TZ).date()
    if last_price is None:
        move_line = (f"A typical hour is expected to move about "
                     f"{hr_move:.2%} up or down. By the end of the day "
                     f"the price is typically about {day_move:.1%} away "
                     f"from where it started. Those are typical sizes, "
                     f"not limits. Bigger days happen regularly.")
    else:
        move_line = (f"A typical hour is expected to move about "
                     f"${last_price * hr_move:,.0f} ({hr_move:.2%}) up or "
                     f"down. By the end of the day the price is typically "
                     f"about ${last_price * day_move:,.0f} "
                     f"({day_move:.1%}) away from where it started, using "
                     f"the last traded price of ${last_price:,.0f}. Those "
                     f"are typical sizes, not limits. Bigger days happen "
                     f"regularly.")
    # One plain phrase per regime word, same percentile bins as `regime`.
    pct_phrase = {"quiet": "below most days of the past year",
                  "normal": "in the middle of the past year's range",
                  "elevated": "above most days of the past year",
                  "high": "among the busiest days of the past year"}[regime]
    lines = [
        f"# Volatility outlook - {day} (generated)",
        "",
        f"**The next 24 hours look {regime} and {trend}.** {move_line}",
        "",
        f"That forecast sits {pct_phrase} (the {pct:.0f}th percentile of "
        f"the past year's rolling 24-hour averages) and works out to about "
        f"{fc_avg:.0%} in annualized units, the per-year convention "
        f"volatility is quoted in. The hourly figures above are that same "
        f"number divided by {ANNUALIZER:.1f}, the square root of the "
        f"hours in a year.",
        "",
        f"- Hourly median forecast ranges {med_path.min():.0%} to "
        f"{med_path.max():.0%} annualized, which is a typical hourly "
        f"move of {med_path.min() / ANNUALIZER:.2%} to "
        f"{med_path.max() / ANNUALIZER:.2%}.",
        high_line,
        f"- The loudest hours are expected around {', '.join(loud)} local "
        f"({LOCAL_TZ}); the calmest around {', '.join(calm)}.",
        f"- Yesterday's realized average was {last24:.0%}, "
        + (f"below the {q_thresh:.0%} quiet line, so yesterday was a "
           f"quiet day by that line." if last24 < q_thresh else
           f"above the {q_thresh:.0%} quiet line, so yesterday was not a "
           f"quiet day."),
        "",
        f"This forecast was produced by {model}, {model_why}. It is a "
        f"volatility outlook only and says nothing about price direction.",
        "",
    ]
    return "\n".join(lines)


def write_outlook(hourly, last_price=None):
    """Render the outlook and save it as results/OUTLOOK.md, returning
    that path for the daily run to commit."""
    path = RESULTS_DIR / "OUTLOOK.md"
    path.write_text(build_outlook(hourly, last_price))
    return path
