import numpy as np
import pandas as pd

from fbench.config import QCOLS, QUANTILES, RESULTS_DIR
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
    ev = _load(EVAL_LOG, ["origin", "target_time", "horizon", "model",
                          *QCOLS, "y_true"])
    if ev["origin"].nunique() >= 3:
        live = score(ev).groupby("model")["pinball_mean"].mean()
        return live.idxmin(), "current live leader"
    return FALLBACK_MODEL, "backtest winner; live sample still small"


def build_outlook(hourly):
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
    pct = float((daily_avg < fc_avg).mean() * 100)
    hi_thresh = float(year.quantile(0.90))
    q_thresh = float(year.quantile(0.30))

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

    local = today["target_time"].dt.tz_convert(LOCAL_TZ)
    order = np.argsort(med_path)
    loud = sorted(local.iloc[order[-3:]].dt.strftime("%H:00"))
    calm = sorted(local.iloc[order[:3]].dt.strftime("%H:00"))

    day = origin.tz_convert(LOCAL_TZ).date()
    lines = [
        f"# Volatility outlook - {day} (generated)",
        "",
        f"**{regime.upper()} and {trend}.** Expected average volatility "
        f"over the next 24 hours: about {fc_avg:.0%} annualized, which is "
        f"the {pct:.0f}th percentile of the past year.",
        "",
        f"- Hourly median forecast ranges {med_path.min():.0%} to "
        f"{med_path.max():.0%}.",
        f"- High-volatility hours (above {hi_thresh:.0%}, the year's 90th "
        f"percentile): about {exp_high_hours:.1f} of the next 24 expected"
        + (f"; {likely_high} hours are more likely than not to qualify."
           if likely_high else "."),
        f"- Loudest hours expected around {', '.join(loud)} local "
        f"({LOCAL_TZ}); calmest around {', '.join(calm)}.",
        f"- Yesterday's realized average was {last24:.0%}; the quiet "
        f"threshold is {q_thresh:.0%}.",
        "",
        f"Forecast model: {model} ({model_why}). This is a volatility "
        f"outlook only; it says nothing about price direction.",
        "",
    ]
    return "\n".join(lines)


def write_outlook(hourly):
    path = RESULTS_DIR / "OUTLOOK.md"
    path.write_text(build_outlook(hourly))
    return path
