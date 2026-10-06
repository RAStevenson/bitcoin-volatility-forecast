"""Scores the claims FORECAST.md made against what happened, one row per
fully resolved forecast day, by replaying the daily forecast's own claim
arithmetic from the evaluation log and the hourly realized series. The
review prints the running record. Every claim is scored in the terms
the daily forecast stated it in, never in a paraphrase: the day move against
the close-to-close price move, the regime and trend words against the
realized day's words, the named hours against the hours that were in
fact loudest and calmest, and the expected count of high hours against
the count that ran high. Beside every claim sits what repeating
yesterday would have scored, because the project's rule is that a
forecast earns its place only past the free alternative, and that rule
binds on the sentences as much as on the hourly bands."""
import numpy as np
import pandas as pd

from fbench.daily_forecast_generator import (
    N_NAMED_HOURS,
    REGIMES,
    claims,
    context,
    distinct_percents,
    leading_model_asof,
    realized_claims,
)
from fbench.harness_config import ANNUALIZER, HORIZON, QCOLS

# Naming three of 24 hours at random would overlap the true three by
# 3 x 3 / 24 hours on average; the record is read against that.
CHANCE_OVERLAP = N_NAMED_HOURS * N_NAMED_HOURS / HORIZON
# A one-standard-deviation move contains about 68% of bell-shaped
# outcomes, the "two days in three" the daily forecast states.
DAY_MOVE_TARGET = 0.68


def day_return(close, origin):
    """Simple close-to-close return from the end of the origin hour to
    the end of the last target hour, or None when either close is
    missing, so a day without price data is skipped rather than scored."""
    end_hour = origin + pd.Timedelta(hours=HORIZON)
    if close is None or origin not in close.index or end_hour not in close.index:
        return None
    start_price, end_price = close.loc[origin], close.loc[end_hour]
    if pd.isna(start_price) or pd.isna(end_price):
        return None
    return float(end_price / start_price - 1)


def score_daily_forecast(evaluations, hourly):
    """One row per fully resolved origin, carrying each claim the daily forecast
    made that morning beside what realized. The reported model is
    re-derived as of the origin, the same way the review names it, and
    the context is the hourly series up to the origin, so the replay sees
    what the daily forecast saw. Days whose reported model lacks a full set of
    rows are skipped. The day-move columns are None when the hourly frame
    carries no close column."""
    target_hours_per_origin = evaluations.groupby("origin")["target_time"].nunique()
    full_origins = sorted(
        target_hours_per_origin[target_hours_per_origin == HORIZON].index)
    close = hourly.get("close")
    rows = []
    for origin in full_origins:
        model = leading_model_asof(evaluations, origin)
        day_evaluations = evaluations[(evaluations["origin"] == origin)
                                      & (evaluations["model"] == model)]
        day_evaluations = day_evaluations.sort_values("target_time")
        if len(day_evaluations) != HORIZON:
            continue
        # log RV -> annualized vol
        annualized_quantiles = np.exp(day_evaluations[QCOLS].to_numpy())
        comparison_context = context(hourly["rv"].loc[:origin])
        forecast_claims = claims(annualized_quantiles, day_evaluations["target_time"],
                                 comparison_context)
        target_realized_vol = hourly["rv"].reindex(
            pd.DatetimeIndex(day_evaluations["target_time"]))
        realized_day_claims = realized_claims(target_realized_vol, comparison_context)
        close_to_close_return = day_return(close, origin)
        # The free alternative for every claim: yesterday, restated. Its
        # regime word is yesterday's, its trend is always steady (the
        # ratio of yesterday to itself), its named hours are yesterday's
        # loudest and calmest at the same clock hours, its high count is
        # yesterday's, and its day move is the same root-sum-of-squares
        # taken over yesterday's realized hours.
        yesterday_realized_vol = hourly["rv"].loc[
            origin - pd.Timedelta(hours=HORIZON - 1):origin]
        yesterday_claims = realized_claims(yesterday_realized_vol, comparison_context)
        one_day = pd.Timedelta(hours=HORIZON)
        yesterday_day_move = float(np.sqrt(np.sum(
            (yesterday_realized_vol.dropna() / ANNUALIZER) ** 2)))
        realized_loud = set(realized_day_claims["loud"])
        realized_calm = set(realized_day_claims["calm"])
        rows.append({
            "origin": origin, "model": model,
            "day_move": forecast_claims["day_move"],
            "day_return": close_to_close_return,
            "day_move_hit": (None if close_to_close_return is None
                             else abs(close_to_close_return)
                             <= forecast_claims["day_move"]),
            "yesterday_day_move_hit": (None if close_to_close_return is None
                                  else abs(close_to_close_return) <= yesterday_day_move),
            "regime_forecast": forecast_claims["regime"],
            "regime_realized": realized_day_claims["regime"],
            "regime_gap": abs(REGIMES.index(forecast_claims["regime"])
                              - REGIMES.index(realized_day_claims["regime"])),
            "yesterday_regime_hit": (yesterday_claims["regime"]
                                == realized_day_claims["regime"]),
            "trend_forecast": forecast_claims["trend"],
            "trend_realized": realized_day_claims["trend"],
            "yesterday_trend_hit": realized_day_claims["trend"] == "steady",
            "loud_overlap": len(set(forecast_claims["loud"]) & realized_loud),
            "calm_overlap": len(set(forecast_claims["calm"]) & realized_calm),
            "yesterday_loud_overlap": len({hour + one_day for hour in yesterday_claims["loud"]}
                                     & realized_loud),
            "yesterday_calm_overlap": len({hour + one_day for hour in yesterday_claims["calm"]}
                                     & realized_calm),
            # On a day when every hour sits at the probability floor the
            # daily forecast prints "no meaningful chance" rather than a count,
            # so the claim it made, and the one scored, is zero hours.
            "expected_high_hours": (0.0 if forecast_claims["all_at_floor"]
                               else forecast_claims["expected_high_hours"]),
            "high_hours": realized_day_claims["high_hours"],
            "yesterday_high_hours": yesterday_claims["high_hours"],
        })
    return pd.DataFrame(rows)


def record_lines(scored):
    """Markdown lines for the review: the most recent resolved day's
    claims against what happened, then the running record over every
    resolved day. Empty when nothing has resolved."""
    if scored.empty:
        return []
    n_days = len(scored)
    latest_day = scored.iloc[-1]
    days_with_price = scored.dropna(subset=["day_move_hit"])
    lines = ["## The daily forecast's own claims", ""]

    latest_sentences = [
        f"On the most recent resolved day the daily forecast called the day "
        f"{latest_day['regime_forecast']} and {latest_day['trend_forecast']}; it turned out "
        f"{latest_day['regime_realized']} and {latest_day['trend_realized']}."]
    if latest_day["day_return"] is not None and not pd.isna(latest_day["day_return"]):
        move_text, ended_text, tie = distinct_percents(
            latest_day["day_move"], abs(latest_day["day_return"]), places=1)
        position_word = ("at" if tie else
                         "inside" if latest_day["day_move_hit"] else "outside")
        latest_sentences.append(
            f"The one-standard-deviation day move was {move_text} and the price "
            f"ended {ended_text} from where it started, {position_word} that "
            f"distance.")
    latest_sentences.append(
        f"{latest_day['loud_overlap']} of the {N_NAMED_HOURS} loudest hours named "
        f"were among the day's {N_NAMED_HOURS} loudest, and "
        f"{latest_day['calm_overlap']} of the {N_NAMED_HOURS} calmest. "
        f"{latest_day['expected_high_hours']:.1f} hours were expected to run high and "
        f"{latest_day['high_hours']} did.")
    lines += [" ".join(latest_sentences), ""]

    lines.append(f"Over {n_days} resolved days, scored in the terms the daily forecast "
                 "states them, with what repeating yesterday would have "
                 "scored beside each claim:")
    lines.append("")
    if len(days_with_price):
        move_hits = int(days_with_price["day_move_hit"].sum())
        yesterday_move_hits = int(days_with_price["yesterday_day_move_hit"].sum())
        n_priced_days = len(days_with_price)
        lines.append(
            f"- The price ended inside the one-standard-deviation day move "
            f"on {move_hits} of {n_priced_days} days "
            f"({move_hits / n_priced_days:.0%}). A "
            f"well-sized move holds about {DAY_MOVE_TARGET:.0%} of days. "
            f"The same distance taken from yesterday's realized hours "
            f"would have held on {yesterday_move_hits}.")
    exact_regime_days = int((scored["regime_gap"] == 0).sum())
    one_step_off_days = int((scored["regime_gap"] == 1).sum())
    far_off_days = int((scored["regime_gap"] >= 2).sum())
    lines.append(
        f"- The regime word (quiet, normal, elevated, high) matched the "
        f"realized day on {exact_regime_days} of {n_days} days, was one step "
        f"off on {one_step_off_days}, and two or more steps off on "
        f"{far_off_days}. Repeating "
        f"yesterday's word would have matched on "
        f"{int(scored['yesterday_regime_hit'].sum())}.")
    trend_hits = int((scored["trend_forecast"] == scored["trend_realized"]).sum())
    lines.append(
        f"- The trend word (rising, steady, falling) matched on "
        f"{trend_hits} of {n_days} days. Always saying steady would have "
        f"matched on {int(scored['yesterday_trend_hit'].sum())}.")
    lines.append(
        f"- Of the {N_NAMED_HOURS} loudest hours named each day, "
        f"{scored['loud_overlap'].mean():.1f} on average were among the "
        f"day's {N_NAMED_HOURS} loudest, and "
        f"{scored['calm_overlap'].mean():.1f} of the {N_NAMED_HOURS} "
        f"calmest. Naming yesterday's loudest and calmest hours again "
        f"would have scored {scored['yesterday_loud_overlap'].mean():.1f} and "
        f"{scored['yesterday_calm_overlap'].mean():.1f}; naming "
        f"{N_NAMED_HOURS} hours at random, {CHANCE_OVERLAP:.1f}.")
    lines.append(
        f"- {scored['expected_high_hours'].sum():.0f} hours were expected to run "
        f"high across those days and {int(scored['high_hours'].sum())} did. "
        f"Yesterday's count, carried forward, would have expected "
        f"{int(scored['yesterday_high_hours'].sum())}.")
    lines.append("")
    return lines
