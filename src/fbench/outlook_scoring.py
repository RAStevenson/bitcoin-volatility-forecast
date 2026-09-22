"""Scores the claims OUTLOOK.md made against what happened, one row per
fully resolved forecast day, by replaying the outlook's own claim
arithmetic from the evaluation log and the hourly realized series. The
review prints the running record. Every claim is scored in the terms
the outlook stated it in, never in a paraphrase: the day move against
the close-to-close price move, the regime and trend words against the
realized day's words, the named hours against the hours that were in
fact loudest and calmest, and the expected count of high hours against
the count that ran high. Beside every claim sits what repeating
yesterday would have scored, because the project's rule is that a
forecast earns its place only past the free alternative, and that rule
binds on the sentences as much as on the hourly bands."""
import numpy as np
import pandas as pd

from fbench.harness_config import ANNUALIZER, HORIZON, QCOLS
from fbench.outlook_generator import (N_NAMED_HOURS, REGIMES, claims, context,
                                      leading_model_asof, realized_claims)

# Naming three of 24 hours at random would overlap the true three by
# 3 x 3 / 24 hours on average; the record is read against that.
CHANCE_OVERLAP = N_NAMED_HOURS * N_NAMED_HOURS / HORIZON
# A one-standard-deviation move contains about 68% of bell-shaped
# outcomes, the "two days in three" the outlook states.
DAY_MOVE_TARGET = 0.68


def day_return(close, origin):
    """Simple close-to-close return from the end of the origin hour to
    the end of the last target hour, or None when either close is
    missing, so a day without price data is skipped rather than scored."""
    end = origin + pd.Timedelta(hours=HORIZON)
    if close is None or origin not in close.index or end not in close.index:
        return None
    start_px, end_px = close.loc[origin], close.loc[end]
    if pd.isna(start_px) or pd.isna(end_px):
        return None
    return float(end_px / start_px - 1)


def score_outlook(ev, hourly):
    """One row per fully resolved origin, carrying each claim the outlook
    made that morning beside what realized. The narrating model is
    re-derived as of the origin, the same way the review names it, and
    the context is the hourly series up to the origin, so the replay sees
    what the outlook saw. Days whose narrating model lacks a full set of
    rows are skipped. The day-move columns are None when the hourly frame
    carries no close column."""
    counts = ev.groupby("origin")["target_time"].nunique()
    full = sorted(counts[counts == HORIZON].index)
    close = hourly["close"] if "close" in hourly else None
    rows = []
    for origin in full:
        model = leading_model_asof(ev, origin)
        day = ev[(ev["origin"] == origin) & (ev["model"] == model)]
        day = day.sort_values("target_time")
        if len(day) != HORIZON:
            continue
        vol = np.exp(day[QCOLS].to_numpy())  # log RV -> annualized vol
        ctx = context(hourly["rv"].loc[:origin])
        c = claims(vol, day["target_time"], ctx)
        target_rv = hourly["rv"].reindex(pd.DatetimeIndex(day["target_time"]))
        r = realized_claims(target_rv, ctx)
        ret = day_return(close, origin)
        # The free alternative for every claim: yesterday, restated. Its
        # regime word is yesterday's, its trend is always steady (the
        # ratio of yesterday to itself), its named hours are yesterday's
        # loudest and calmest at the same clock hours, its high count is
        # yesterday's, and its day move is the same root-sum-of-squares
        # taken over yesterday's realized hours.
        yesterday = hourly["rv"].loc[origin - pd.Timedelta(hours=HORIZON - 1):origin]
        y = realized_claims(yesterday, ctx)
        shift = pd.Timedelta(hours=HORIZON)
        base_move = float(np.sqrt(np.sum((yesterday.dropna() / ANNUALIZER) ** 2)))
        rows.append({
            "origin": origin, "model": model,
            "day_move": c["day_move"], "day_return": ret,
            "day_move_hit": None if ret is None else abs(ret) <= c["day_move"],
            "base_day_move_hit": None if ret is None else abs(ret) <= base_move,
            "regime_fc": c["regime"], "regime_rz": r["regime"],
            "regime_gap": abs(REGIMES.index(c["regime"])
                              - REGIMES.index(r["regime"])),
            "base_regime_hit": y["regime"] == r["regime"],
            "trend_fc": c["trend"], "trend_rz": r["trend"],
            "base_trend_hit": r["trend"] == "steady",
            "loud_overlap": len(set(c["loud"]) & set(r["loud"])),
            "calm_overlap": len(set(c["calm"]) & set(r["calm"])),
            "base_loud_overlap": len({t + shift for t in y["loud"]} & set(r["loud"])),
            "base_calm_overlap": len({t + shift for t in y["calm"]} & set(r["calm"])),
            # On a day when every hour sits at the probability floor the
            # outlook prints "no meaningful chance" rather than a count,
            # so the claim it made, and the one scored, is zero hours.
            "exp_high_hours": 0.0 if c["all_at_floor"] else c["exp_high_hours"],
            "high_hours": r["high_hours"],
            "base_high_hours": y["high_hours"],
        })
    return pd.DataFrame(rows)


def record_lines(scored):
    """Markdown lines for the review: the most recent resolved day's
    claims against what happened, then the running record over every
    resolved day. Empty when nothing has resolved."""
    if scored.empty:
        return []
    n = len(scored)
    last = scored.iloc[-1]
    moves = scored.dropna(subset=["day_move_hit"])
    lines = ["## The outlook's own claims", ""]

    latest = [f"On the most recent resolved day the outlook called the day "
              f"{last['regime_fc']} and {last['trend_fc']}; it turned out "
              f"{last['regime_rz']} and {last['trend_rz']}."]
    if last["day_return"] is not None and not pd.isna(last["day_return"]):
        latest.append(
            f"The one-standard-deviation day move was {last['day_move']:.1%} "
            f"and the price ended {abs(last['day_return']):.1%} from where "
            f"it started, "
            f"{'inside' if last['day_move_hit'] else 'outside'} that "
            f"distance.")
    latest.append(
        f"{last['loud_overlap']} of the {N_NAMED_HOURS} loudest hours named "
        f"were among the day's {N_NAMED_HOURS} loudest, and "
        f"{last['calm_overlap']} of the {N_NAMED_HOURS} calmest. "
        f"{last['exp_high_hours']:.1f} hours were expected to run high and "
        f"{last['high_hours']} did.")
    lines += [" ".join(latest), ""]

    lines.append(f"Over {n} resolved days, scored in the terms the outlook "
                 "states them, with what repeating yesterday would have "
                 "scored beside each claim:")
    lines.append("")
    if len(moves):
        hits = int(moves["day_move_hit"].sum())
        base_hits = int(moves["base_day_move_hit"].sum())
        lines.append(
            f"- The price ended inside the one-standard-deviation day move "
            f"on {hits} of {len(moves)} days ({hits / len(moves):.0%}). A "
            f"well-sized move holds about {DAY_MOVE_TARGET:.0%} of days. "
            f"The same distance taken from yesterday's realized hours "
            f"would have held on {base_hits}.")
    exact = int((scored["regime_gap"] == 0).sum())
    adjacent = int((scored["regime_gap"] == 1).sum())
    far = int((scored["regime_gap"] >= 2).sum())
    lines.append(
        f"- The regime word (quiet, normal, elevated, high) matched the "
        f"realized day on {exact} of {n} days, was one step off on "
        f"{adjacent}, and two or more steps off on {far}. Repeating "
        f"yesterday's word would have matched on "
        f"{int(scored['base_regime_hit'].sum())}.")
    trend_hits = int((scored["trend_fc"] == scored["trend_rz"]).sum())
    lines.append(
        f"- The trend word (rising, steady, falling) matched on "
        f"{trend_hits} of {n} days. Always saying steady would have "
        f"matched on {int(scored['base_trend_hit'].sum())}.")
    lines.append(
        f"- Of the {N_NAMED_HOURS} loudest hours named each day, "
        f"{scored['loud_overlap'].mean():.1f} on average were among the "
        f"day's {N_NAMED_HOURS} loudest, and "
        f"{scored['calm_overlap'].mean():.1f} of the {N_NAMED_HOURS} "
        f"calmest. Naming yesterday's loudest and calmest hours again "
        f"would have scored {scored['base_loud_overlap'].mean():.1f} and "
        f"{scored['base_calm_overlap'].mean():.1f}; naming "
        f"{N_NAMED_HOURS} hours at random, {CHANCE_OVERLAP:.1f}.")
    lines.append(
        f"- {scored['exp_high_hours'].sum():.0f} hours were expected to run "
        f"high across those days and {int(scored['high_hours'].sum())} did. "
        f"Yesterday's count, carried forward, would have expected "
        f"{int(scored['base_high_hours'].sum())}.")
    lines.append("")
    return lines
