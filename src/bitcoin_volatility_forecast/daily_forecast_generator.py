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

from bitcoin_volatility_forecast.daily_run import EVAL_LOG, FORECAST_LOG, _load, expected_vol
from bitcoin_volatility_forecast.forecast_settings import (
    ANNUALIZER,
    QCOLS,
    QUANTILES,
    RELEASE_ORIGIN,
    RESULTS_DIR,
)
from bitcoin_volatility_forecast.quantile_scoring import score

LOCAL_TZ = "America/Chicago"
FALLBACK_MODEL = "nhits"  # winner of the pinned backtest, used until live scores exist
REGIMES = ["quiet", "normal", "elevated", "high"]
N_NAMED_HOURS = 3  # the loudest and calmest hours the daily forecast names


# Five quantiles cannot say "no chance", so a probability read off them
# is clamped at this floor. Summed over 24 hours the floor alone is 0.48
# expected high hours, which is why the forecast prints a count only when
# the count exceeds that floor by MIN_HIGH_HOURS_ABOVE_FLOOR; below it,
# the number would be mostly the clamp, not a forecast (reader panel,
# 2026-10-21: on a quiet day "about 0.5 hours" was 0.46 of floor).
PROBABILITY_FLOOR = 0.02
MIN_HIGH_HOURS_ABOVE_FLOOR = 0.5


def prob_above(vol_quantiles, threshold):
    """P(X > threshold) by linear interpolation on the five known CDF
    points, clamped to [PROBABILITY_FLOOR, 1 - PROBABILITY_FLOOR] beyond
    the tails. Works per hour on marginal quantiles; no independence
    assumption is ever layered on."""
    cumulative_probability = np.interp(threshold, vol_quantiles, QUANTILES,
                                       left=PROBABILITY_FLOOR,
                                       right=1.0 - PROBABILITY_FLOOR)
    return float(1.0 - cumulative_probability)


def _live_leader(evaluations):
    """The model with the lowest mean pinball loss over the resolved rows
    in evaluations, or None while fewer than three origins have been scored."""
    # Three origins is a deliberately lower bar than the 10-day gate on
    # LIVE.md's matched-day skill: picking which model the daily forecast
    # reports only needs a best guess, while the skill line is a published
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


def context(realized_vol_to_origin):
    """Everything a day is compared against, from the hourly realized
    series up to the origin: the past year of hours, its rolling 24-hour
    averages, the high line (the year's 90th percentile hour), the quiet
    line (the 30th percentile of the daily averages) and the average of
    the 24 hours before the origin."""
    realized_vol = realized_vol_to_origin.dropna()
    year_start = realized_vol.index.max() - pd.Timedelta(days=365)
    year = realized_vol.loc[realized_vol.index >= year_start]
    daily_averages = year.rolling(24).mean().dropna()
    # The quiet/normal boundary compares a 24-hour average to the
    # distribution of rolling 24h averages, so the printed threshold must
    # come from the same distribution or it is not the deciding line.
    return {"year": year, "daily_averages": daily_averages,
            "high_line": float(year.quantile(0.90)),
            "quiet_line": float(daily_averages.quantile(0.30)),
            "previous_day_average": float(realized_vol.iloc[-24:].mean())}


def ordinal(number):
    """Return number with its English ordinal suffix, as in 3 to 3rd and
    31 to 31st, for generated sentences that place a value by rank or
    percentile."""
    suffix = ("th" if 10 <= number % 100 <= 20
              else {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th"))
    return f"{number}{suffix}"


def regime_of(day_average, daily_averages):
    """The regime word for a 24-hour average of annualized volatility,
    placed against the past year's rolling 24-hour averages, returned
    with the percentile it sits at."""
    percentile = float((daily_averages < day_average).mean() * 100)
    word = ("quiet" if percentile < 30 else
            "normal" if percentile < 70 else
            "elevated" if percentile < 90 else "high")
    return word, percentile


def trend_of(day_average, previous_day_average):
    """The trend word for a 24-hour average against the average of the
    24 hours before the origin: rising past a tenth up, falling past a
    tenth down, steady between."""
    ratio = day_average / previous_day_average
    return ("rising" if ratio > 1.10 else
            "falling" if ratio < 0.90 else "steady")


def uses_expected_value(target_times):
    """Whether a forecast over target_times falls under the expected-value
    day figure, which applies from RELEASE_ORIGIN on (see day_path)."""
    origin = pd.DatetimeIndex(target_times)[0] - pd.Timedelta(hours=1)
    return bool(origin >= pd.Timestamp(RELEASE_ORIGIN, tz="UTC"))


def day_path(annualized_quantiles, target_times):
    """The 24 hourly values whose average is the forecast of the day's
    average volatility. From RELEASE_ORIGIN on, each hour's expected
    volatility (daily_run.expected_vol); before it, the hourly median,
    which is what the forecast page printed on those days, so the review
    replays each past day's claim as it was made rather than as the
    current rule would make it."""
    if uses_expected_value(target_times):
        log_quantiles = dict(zip(QCOLS, np.log(annualized_quantiles).T, strict=True))
        return expected_vol(log_quantiles)
    return annualized_quantiles[:, 2]


def claims(annualized_quantiles, target_times, comparison_context):
    """The numbers behind every claim the daily forecast makes, from the
    reported model's 24 rows of annualized quantiles (one row per target
    hour, columns in QUANTILES order) and the context as of the origin:
    the typical hourly move, the one-standard-deviation day move, the
    regime and trend words, the expected count of hours above the high
    line, and which target hours are named loudest and calmest."""
    median_path = annualized_quantiles[:, 2]
    forecast_average = float(day_path(annualized_quantiles, target_times).mean())
    # Human translation: annualized vol / sqrt(hours per year) is the
    # typical single-hour move. The daily figure is the root of summed
    # hourly variances, a one-sigma close-to-close move rather than a
    # range; averaging the hourly sigmas first would understate it
    # whenever vol varies across the day.
    regime, percentile = regime_of(forecast_average, comparison_context["daily_averages"])
    high_probabilities = [prob_above(hour_quantiles, comparison_context["high_line"])
                          for hour_quantiles in annualized_quantiles]
    expected_high_hours = float(np.sum(high_probabilities))
    floor_total = PROBABILITY_FLOOR * len(high_probabilities)
    positions_by_median = np.argsort(median_path)
    target_hours = pd.DatetimeIndex(target_times)
    return {
        "forecast_average": forecast_average, "median_path": median_path,
        "expected_value_rule": uses_expected_value(target_times),
        # The typical hour is the median hour, so this stays on the
        # medians whichever rule the day figure uses.
        "hourly_move": float(median_path.mean()) / ANNUALIZER,
        "day_move": float(np.sqrt(np.sum((median_path / ANNUALIZER) ** 2))),
        "regime": regime, "percentile": percentile,
        "trend": trend_of(forecast_average, comparison_context["previous_day_average"]),
        "high_probabilities": high_probabilities,
        "expected_high_hours": expected_high_hours,
        "likely_high": int(np.sum(np.array(high_probabilities) > 0.5)),
        # The count is a forecast only in the part above the clamp floor;
        # see PROBABILITY_FLOOR. all_at_floor is the limiting case, where
        # every band sits below the line, and it only shapes the wording.
        "no_meaningful_high": (expected_high_hours - floor_total
                               < MIN_HIGH_HOURS_ABOVE_FLOOR),
        "all_at_floor": all(probability <= PROBABILITY_FLOOR + 1e-9
                            for probability in high_probabilities),
        "loud": target_hours[positions_by_median[-N_NAMED_HOURS:]],
        "calm": target_hours[positions_by_median[:N_NAMED_HOURS]],
    }


def realized_claims(target_realized_vol, comparison_context):
    """What happened over the target hours, stated in the terms of
    claims(): the realized 24-hour average with its regime and trend
    words against the same context, the hours that were in fact loudest
    and calmest, and how many hours ran above the high line.
    target_realized_vol is the realized annualized volatility indexed by
    target hour."""
    realized_vol = target_realized_vol.dropna()
    realized_average = float(realized_vol.mean())
    regime, percentile = regime_of(realized_average, comparison_context["daily_averages"])
    positions_by_realized = np.argsort(realized_vol.to_numpy())
    return {"realized_average": realized_average, "regime": regime, "percentile": percentile,
            "trend": trend_of(realized_average, comparison_context["previous_day_average"]),
            "loud": realized_vol.index[positions_by_realized[-N_NAMED_HOURS:]],
            "calm": realized_vol.index[positions_by_realized[:N_NAMED_HOURS]],
            "high_hours": int((realized_vol > comparison_context["high_line"]).sum())}


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
    model, model_reason = _leading_model()
    origin = forecasts["origin"].max()
    todays_forecasts = forecasts[(forecasts["origin"] == origin)
                                 & (forecasts["model"] == model)].copy()
    todays_forecasts = todays_forecasts.sort_values("target_time")
    # log RV -> annualized vol
    annualized_quantiles = np.exp(todays_forecasts[QCOLS].to_numpy())

    comparison_context = context(hourly["rv"].loc[:origin])
    forecast_claims = claims(annualized_quantiles, todays_forecasts["target_time"],
                             comparison_context)
    median_path = forecast_claims["median_path"]
    forecast_average = forecast_claims["forecast_average"]
    hourly_move, day_move = forecast_claims["hourly_move"], forecast_claims["day_move"]
    high_threshold = comparison_context["high_line"]
    quiet_threshold = comparison_context["quiet_line"]
    previous_day_average = comparison_context["previous_day_average"]

    high_hourly_move = high_threshold / ANNUALIZER
    if forecast_claims["no_meaningful_high"]:
        high_line = (f"- No hour shows a meaningful chance of running "
                     f"high, above {high_threshold:.0%} annualized (an hourly "
                     f"move over {high_hourly_move:.2%}), higher than 90% of "
                     f"individual hours in the past year"
                     + ("; every forecast band sits well below that line."
                        if forecast_claims["all_at_floor"] else "."))
    else:
        high_line = (f"- The next 24 hours are expected to include about "
                     f"{forecast_claims['expected_high_hours']:.1f} hours running "
                     f"high, above "
                     f"{high_threshold:.0%} annualized (an hourly move over "
                     f"{high_hourly_move:.2%}), higher than 90% of individual "
                     f"hours in the past year"
                     + (f"; {forecast_claims['likely_high']} hours are more "
                        f"likely than not to qualify."
                        if forecast_claims["likely_high"] else "."))

    loudest_hours = sorted(
        forecast_claims["loud"].tz_convert(LOCAL_TZ).strftime("%H:00"))
    calmest_hours = sorted(
        forecast_claims["calm"].tz_convert(LOCAL_TZ).strftime("%H:00"))

    day = origin.tz_convert(LOCAL_TZ).date()
    if last_price is None:
        move_line = (f"A typical hour is expected to move about "
                     f"{hourly_move:.2%} up or down. Combining the 24 hourly "
                     f"forecasts gives a one-standard-deviation move of "
                     f"about {day_move:.1%} for the whole day. On about "
                     f"two days in three the price ends within that "
                     f"distance of where it started, which is what one "
                     f"standard deviation means when the day's move is "
                     f"roughly bell-shaped. Bigger days happen regularly.")
    else:
        move_line = (f"A typical hour is expected to move about "
                     f"${last_price * hourly_move:,.0f} ({hourly_move:.2%}) up or "
                     f"down. Combining the 24 hourly forecasts gives a "
                     f"one-standard-deviation move of about "
                     f"${last_price * day_move:,.0f} ({day_move:.1%}) for "
                     f"the whole day, using the last traded price of "
                     f"${last_price:,.0f}. On about two days in three the "
                     f"price ends within that distance of where it "
                     f"started, which is what one standard deviation "
                     f"means when the day's move is roughly bell-shaped. "
                     f"Bigger days happen regularly.")
    # How the annualized day figure relates to the typical-hour move
    # above. Under the expected-value rule the two come from different
    # paths (see day_path), so the page says which is which.
    if forecast_claims["expected_value_rule"]:
        annualized_note = (
            f"Each hour's figure in that average is its expected volatility, "
            f"which sits a little above the hour's median because the big hours "
            f"pull an average up more than they move a median. The "
            f"typical-hour move above is the average of the 24 hourly "
            f"medians divided by {ANNUALIZER:.1f}, the square root of the "
            f"hours in a year.")
    else:
        annualized_note = (f"The hourly figures above are that same number "
                           f"divided by {ANNUALIZER:.1f}, the square root of the "
                           f"hours in a year.")
    # One plain phrase per regime word, same percentile bins as regime_of.
    percentile_phrase = {"quiet": "below most days of the past year",
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
        f"That forecast sits {percentile_phrase} (the "
        f"{ordinal(round(forecast_claims['percentile']))} percentile of "
        f"the past year's rolling 24-hour averages). Averaged over its 24 "
        f"hourly volatilities, it works out to about {forecast_average:.0%} in "
        f"annualized units, the per-year convention volatility is quoted in. "
        + annualized_note,
        "",
        f"- Hourly median forecast ranges {median_path.min():.0%} to "
        f"{median_path.max():.0%} annualized, which is a typical hourly "
        f"move of {median_path.min() / ANNUALIZER:.2%} to "
        f"{median_path.max() / ANNUALIZER:.2%}.",
        high_line,
        f"- The loudest hours are expected around {', '.join(loudest_hours)} "
        f"local ({LOCAL_TZ}); the calmest around {', '.join(calmest_hours)}.",
        _quiet_line_sentence(previous_day_average, quiet_threshold),
        "",
        f"This forecast was produced by {model}, {model_reason}. It is a "
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


def _quiet_line_sentence(previous_day_average, quiet_threshold):
    """The bullet comparing yesterday's realized average with the quiet
    line. Both print as whole percents unless they round to the same
    one, in which case a decimal place is added, then a second, so the
    sentence never reads "30%, above the 30% quiet line". Values still
    equal at two places are said to sit at the line, which does not
    count as below it. The quiet-or-not clause is this sentence's own
    strict comparison with the printed line; the regime word elsewhere
    in the forecast is decided separately, by regime_of."""
    average_text, line_text, tie = distinct_percents(previous_day_average,
                                                     quiet_threshold)
    position_word = ("at" if tie else
                     "below" if previous_day_average < quiet_threshold else "above")
    quiet_clause = ("so yesterday was a quiet day by that line."
                    if position_word == "below" else "so yesterday was not a quiet day.")
    return (f"- Yesterday's realized average was {average_text}, {position_word} the "
            f"{line_text} "
            f"quiet line, {quiet_clause}")


def write_daily_forecast(hourly, last_price=None):
    """Render the daily forecast and save it as results/FORECAST.md, returning
    that path for the daily run to commit."""
    path = RESULTS_DIR / "FORECAST.md"
    path.write_text(build_daily_forecast(hourly, last_price))
    return path
