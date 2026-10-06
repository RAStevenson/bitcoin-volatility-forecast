"""Builds results/FORECAST.md, the plain-language read of the latest
logged 24-hour forecast for someone who does not work in volatility.
Every figure is derived at render time from the forecast log and the
hourly realized series, so the prose cannot drift away from the
numbers. The arithmetic behind every claim the daily forecast makes lives in
claims(), and realized_claims() states what happened in the same terms,
so the review's daily forecast scoring replays the claims the daily forecast actually
made rather than a paraphrase of them."""
import numpy as np
import pandas as pd

from fbench.daily_run import EVAL_LOG, FORECAST_LOG, _load
from fbench.harness_config import ANNUALIZER, QCOLS, QUANTILES, RESULTS_DIR
from fbench.quantile_scoring import score

LOCAL_TZ = "America/Chicago"
FALLBACK_MODEL = "nhits"  # winner of the pinned backtest, used until live scores exist
REGIMES = ["quiet", "normal", "elevated", "high"]
N_NAMED_HOURS = 3  # the loudest and calmest hours the daily forecast names


def prob_above(vol_quantiles, threshold):
    """P(X > threshold) by linear interpolation on the five known CDF
    points, clamped to [0.02, 0.98] beyond the tails. Works per hour on
    marginal quantiles; no independence assumption is ever layered on."""
    cdf = np.interp(threshold, vol_quantiles, QUANTILES,
                    left=0.02, right=0.98)
    return float(1.0 - cdf)


def _live_leader(evaluations):
    """The model with the lowest mean pinball loss over the resolved rows
    in evaluations, or None while fewer than three origins have been scored."""
    # Three origins is a deliberately lower bar than the 10-day
    # calibration gate: picking which model the daily forecast reports only
    # needs a best guess, while the calibration line is a published
    # result, so that one waits for the larger sample.
    if evaluations["origin"].nunique() >= 3:
        return score(evaluations).groupby("model")["pinball_mean"].mean().idxmin()
    return None


def _leading_model():
    """Pick the model the daily forecast reports and return it with the
    short phrase explaining the choice, which is the live pinball leader
    once three origins have been scored and FALLBACK_MODEL before that."""
    evaluations = _load(EVAL_LOG, ["origin", "target_time", "horizon", "model",
                                   *QCOLS, "y_true"])
    leader = _live_leader(evaluations)
    if leader is not None:
        return leader, "the model currently leading the daily record"
    return FALLBACK_MODEL, "the backtest winner while the live sample is young"


def leading_model_asof(evaluations, origin):
    """The model the daily forecast issued at `origin` reported, re-derived
    from the scores that existed then (origins strictly earlier)."""
    leader = _live_leader(evaluations[evaluations["origin"] < origin])
    if leader is not None:
        return leader
    # The fallback may not be in the log (a trimmed registry); reporting
    # a model with no rows would print NaN prose, so require presence.
    day_models = evaluations.loc[evaluations["origin"] == origin, "model"].unique()
    if FALLBACK_MODEL in day_models:
        return FALLBACK_MODEL
    return sorted(day_models)[0]


def context(rv_asof):
    """Everything a day is compared against, from the hourly realized
    series up to the origin: the past year of hours, its rolling 24-hour
    averages, the high line (the year's 90th percentile hour), the quiet
    line (the 30th percentile of the daily averages) and the average of
    the 24 hours before the origin."""
    realized_vol = rv_asof.dropna()
    year_start = realized_vol.index.max() - pd.Timedelta(days=365)
    year = realized_vol.loc[realized_vol.index >= year_start]
    daily_avg = year.rolling(24).mean().dropna()
    # The quiet/normal boundary compares a 24-hour average to the
    # distribution of rolling 24h averages, so the printed threshold must
    # come from the same distribution or it is not the deciding line.
    return {"year": year, "daily_avg": daily_avg,
            "hi_thresh": float(year.quantile(0.90)),
            "q_thresh": float(daily_avg.quantile(0.30)),
            "last24": float(realized_vol.iloc[-24:].mean())}


def regime_of(avg, daily_avg):
    """The regime word for a 24-hour average of annualized volatility,
    placed against the past year's rolling 24-hour averages, returned
    with the percentile it sits at."""
    pct = float((daily_avg < avg).mean() * 100)
    word = ("quiet" if pct < 30 else
            "normal" if pct < 70 else
            "elevated" if pct < 90 else "high")
    return word, pct


def trend_of(avg, last24):
    """The trend word for a 24-hour average against the average of the
    24 hours before the origin: rising past a tenth up, falling past a
    tenth down, steady between."""
    ratio = avg / last24
    return ("rising" if ratio > 1.10 else
            "falling" if ratio < 0.90 else "steady")


def claims(vol, target_times, ctx):
    """The numbers behind every claim the daily forecast makes, from the
    reported model's 24 rows of annualized quantiles (vol, one row per
    target hour, columns in QUANTILES order) and the context as of the
    origin: the typical hourly move, the one-standard-deviation day move,
    the regime and trend words, the expected count of hours above the
    high line, and which target hours are named loudest and calmest."""
    med_path = vol[:, 2]
    fc_avg = float(med_path.mean())
    # Human translation: annualized vol / sqrt(hours per year) is the
    # typical single-hour move. The daily figure is the root of summed
    # hourly variances, a one-sigma close-to-close move rather than a
    # range; averaging the hourly sigmas first would understate it
    # whenever vol varies across the day.
    regime, pct = regime_of(fc_avg, ctx["daily_avg"])
    p_high = [prob_above(vol[i], ctx["hi_thresh"]) for i in range(len(vol))]
    order = np.argsort(med_path)
    target_hours = pd.DatetimeIndex(target_times)
    return {
        "fc_avg": fc_avg, "med_path": med_path,
        "hr_move": fc_avg / ANNUALIZER,
        "day_move": float(np.sqrt(np.sum((med_path / ANNUALIZER) ** 2))),
        "regime": regime, "pct": pct,
        "trend": trend_of(fc_avg, ctx["last24"]),
        "p_high": p_high,
        "exp_high_hours": float(np.sum(p_high)),
        "likely_high": int(np.sum(np.array(p_high) > 0.5)),
        # prob_above clamps at 0.02 beyond the fitted quantiles, so when
        # every hour sits at the clamp the sum is a floor (24 x 0.02), not
        # a forecast, and printing it as one would dress a constant as
        # information.
        "all_at_floor": all(probability <= 0.02 + 1e-9 for probability in p_high),
        "loud": target_hours[order[-N_NAMED_HOURS:]],
        "calm": target_hours[order[:N_NAMED_HOURS]],
    }


def realized_claims(target_rv, ctx):
    """What happened over the target hours, stated in the terms of
    claims(): the realized 24-hour average with its regime and trend
    words against the same context, the hours that were in fact loudest
    and calmest, and how many hours ran above the high line. target_rv is
    the realized annualized volatility indexed by target hour."""
    realized_vol = target_rv.dropna()
    rz_avg = float(realized_vol.mean())
    regime, pct = regime_of(rz_avg, ctx["daily_avg"])
    order = np.argsort(realized_vol.to_numpy())
    return {"rz_avg": rz_avg, "regime": regime, "pct": pct,
            "trend": trend_of(rz_avg, ctx["last24"]),
            "loud": realized_vol.index[order[-N_NAMED_HOURS:]],
            "calm": realized_vol.index[order[:N_NAMED_HOURS]],
            "high_hours": int((realized_vol > ctx["hi_thresh"]).sum())}


def build_daily_forecast(hourly, last_price=None):
    """Return the Markdown body of the daily forecast, turning the leading
    model's latest 24-hour quantiles into typical hourly and daily move
    sizes, a regime word set against the past year, and the loud and calm
    hours ahead. Without last_price the moves are quoted in percent only,
    since a dollar figure has no price to hang on."""
    forecasts = _load(FORECAST_LOG, ["origin", "target_time", "horizon", "model",
                                     *QCOLS])
    if forecasts.empty:
        return "# Volatility forecast\n\nNo forecasts logged yet.\n"
    model, model_why = _leading_model()
    origin = forecasts["origin"].max()
    today = forecasts[(forecasts["origin"] == origin)
                      & (forecasts["model"] == model)].copy()
    today = today.sort_values("target_time")
    vol = np.exp(today[QCOLS].to_numpy())  # log RV -> annualized vol

    ctx = context(hourly["rv"].loc[:origin])
    forecast_claims = claims(vol, today["target_time"], ctx)
    med_path, fc_avg = forecast_claims["med_path"], forecast_claims["fc_avg"]
    hr_move, day_move = forecast_claims["hr_move"], forecast_claims["day_move"]
    hi_thresh, q_thresh, last24 = ctx["hi_thresh"], ctx["q_thresh"], ctx["last24"]

    hi_move = hi_thresh / ANNUALIZER
    if forecast_claims["all_at_floor"]:
        high_line = (f"- No hour shows a meaningful chance of running "
                     f"high, above {hi_thresh:.0%} annualized (an hourly "
                     f"move over {hi_move:.2%}), higher than 90% of "
                     f"individual hours in the past year; every forecast "
                     f"band sits well below that line.")
    else:
        high_line = (f"- The next 24 hours are expected to include about "
                     f"{forecast_claims['exp_high_hours']:.1f} hours running "
                     f"high, above "
                     f"{hi_thresh:.0%} annualized (an hourly move over "
                     f"{hi_move:.2%}), higher than 90% of individual "
                     f"hours in the past year"
                     + (f"; {forecast_claims['likely_high']} hours are more "
                        f"likely than not to qualify."
                        if forecast_claims["likely_high"] else "."))

    loud = sorted(forecast_claims["loud"].tz_convert(LOCAL_TZ).strftime("%H:00"))
    calm = sorted(forecast_claims["calm"].tz_convert(LOCAL_TZ).strftime("%H:00"))

    day = origin.tz_convert(LOCAL_TZ).date()
    if last_price is None:
        move_line = (f"A typical hour is expected to move about "
                     f"{hr_move:.2%} up or down. Combining the 24 hourly "
                     f"forecasts gives a one-standard-deviation move of "
                     f"about {day_move:.1%} for the whole day. On about "
                     f"two days in three the price ends within that "
                     f"distance of where it started, which is what one "
                     f"standard deviation means when the day's move is "
                     f"roughly bell-shaped. Bigger days happen regularly.")
    else:
        move_line = (f"A typical hour is expected to move about "
                     f"${last_price * hr_move:,.0f} ({hr_move:.2%}) up or "
                     f"down. Combining the 24 hourly forecasts gives a "
                     f"one-standard-deviation move of about "
                     f"${last_price * day_move:,.0f} ({day_move:.1%}) for "
                     f"the whole day, using the last traded price of "
                     f"${last_price:,.0f}. On about two days in three the "
                     f"price ends within that distance of where it "
                     f"started, which is what one standard deviation "
                     f"means when the day's move is roughly bell-shaped. "
                     f"Bigger days happen regularly.")
    # One plain phrase per regime word, same percentile bins as regime_of.
    pct_phrase = {"quiet": "below most days of the past year",
                  "normal": "in the middle of the past year's range",
                  "elevated": "above most days of the past year",
                  "high": "among the busiest days of the past year",
                  }[forecast_claims["regime"]]
    lines = [
        f"# Volatility forecast - {day} (generated)",
        "",
        f"**The next 24 hours look {forecast_claims['regime']} and "
        f"{forecast_claims['trend']}.** {move_line}",
        "",
        f"That forecast sits {pct_phrase} (the {forecast_claims['pct']:.0f}th "
        f"percentile of "
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
        _quiet_line_sentence(last24, q_thresh),
        "",
        f"This forecast was produced by {model}, {model_why}. It is a "
        f"volatility forecast only and says nothing about price direction.",
        "",
    ]
    return "\n".join(lines)


def distinct_percents(first, second, places=0, extra=2):
    """Format two fractions as percents for a sentence that compares
    them, starting at `places` decimals and adding up to `extra` more
    only while the two would print the same. Returns the two strings
    and whether they still print the same, which the caller words as a
    tie. Rounding both sides to the same number and then calling one
    larger is the fault this prevents."""
    first_text, second_text = f"{first:.{places}%}", f"{second:.{places}%}"
    for decimals in range(places, places + extra + 1):
        first_text, second_text = f"{first:.{decimals}%}", f"{second:.{decimals}%}"
        if first_text != second_text:
            return first_text, second_text, False
    return first_text, second_text, True


def _quiet_line_sentence(last24, q_thresh):
    """The bullet comparing yesterday's realized average with the quiet
    line. Both print as whole percents unless they round to the same
    one, in which case a decimal place is added, then a second, so the
    sentence never reads "30%, above the 30% quiet line". Values still
    equal at two places are said to sit at the line, which does not
    count as below it. The quiet-or-not clause is this sentence's own
    strict comparison with the printed line; the regime word elsewhere
    in the forecast is decided separately, by regime_of."""
    last24_text, line_text, tie = distinct_percents(last24, q_thresh)
    where = "at" if tie else "below" if last24 < q_thresh else "above"
    quiet = ("so yesterday was a quiet day by that line."
             if where == "below" else "so yesterday was not a quiet day.")
    return (f"- Yesterday's realized average was {last24_text}, {where} the "
            f"{line_text} "
            f"quiet line, {quiet}")


def write_daily_forecast(hourly, last_price=None):
    """Render the daily forecast and save it as results/FORECAST.md, returning
    that path for the daily run to commit."""
    path = RESULTS_DIR / "FORECAST.md"
    path.write_text(build_daily_forecast(hourly, last_price))
    return path
