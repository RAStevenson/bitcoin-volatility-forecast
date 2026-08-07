import pandas as pd

from fbench.config import (COV90_BAND, HORIZON, MIN_CALIBRATION_DAYS,
                           QCOLS, RESULTS_DIR)
from fbench.models.base import REGISTRY
from fbench.scoring import add_skill, score

FORECAST_LOG = RESULTS_DIR / "forecasts.csv"
EVAL_LOG = RESULTS_DIR / "evaluation.csv"
LOG_COLS = ["origin", "target_time", "horizon", "model"] + QCOLS


def _load(path, cols):
    if not path.exists():
        return pd.DataFrame(columns=cols)
    df = pd.read_csv(path)
    for c in ("origin", "target_time"):
        df[c] = pd.to_datetime(df[c], utc=True)
    return df


def log_forecasts(feats, origin):
    """Append one 24-hour quantile forecast per registered model, fit on
    data up to origin. Idempotent by (origin, model): rows already logged
    for this origin are never rewritten - the log is pre-outcome evidence
    and must be append-only."""
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
        frames = ([existing] if len(existing) else []) + added
        out = pd.concat(frames, ignore_index=True)[LOG_COLS]
        RESULTS_DIR.mkdir(exist_ok=True)
        out.to_csv(FORECAST_LOG, index=False)
    return sum(len(a) for a in added)


def score_due(hourly):
    """Resolve forecast rows whose target hour now has an actual and which
    are not yet in the evaluation log. Returns rows resolved."""
    fc = _load(FORECAST_LOG, LOG_COLS)
    ev = _load(EVAL_LOG, LOG_COLS + ["y_true"])
    seen = set(zip(ev["origin"], ev["target_time"], ev["model"]))
    pend = fc[~fc.apply(lambda r: (r["origin"], r["target_time"],
                                   r["model"]) in seen, axis=1)].copy()
    if pend.empty:
        return 0
    pend["y_true"] = hourly["log_rv"].reindex(
        pd.DatetimeIndex(pend["target_time"])).to_numpy()
    resolved = pend.dropna(subset=["y_true"])
    if resolved.empty:
        return 0
    out = pd.concat([ev, resolved], ignore_index=True)
    out.to_csv(EVAL_LOG, index=False)
    return len(resolved)


def calibration_lines(per_model, days):
    """Sample-gated cov90 verdict for the live report. Below the day
    minimum the pooled coverage rate is dominated by within-day
    dependence (3 clean quiet days once produced cov90 = 1.0 from
    models the year-long backtest shows are calibrated), so the check
    stays inactive rather than crying wolf."""
    lo, hi = COV90_BAND
    if days < MIN_CALIBRATION_DAYS:
        return [f"The calibration check stays inactive until "
                f"{MIN_CALIBRATION_DAYS} scored days ({days} so far). "
                "Coverage columns are provisional; each day contributes "
                "~24 dependent hourly rows, so the effective sample is "
                "the day count.", ""]
    flagged = per_model[(per_model["cov90"] < lo) | (per_model["cov90"] > hi)]
    if flagged.empty:
        return [f"The calibration check passes, with all models inside "
                f"the cov90 band [{lo:.2f}, {hi:.2f}] over {days} scored "
                "days.", ""]
    parts = "; ".join(f"{m} {v:.4f}" for m, v in flagged["cov90"].items())
    return [f"The calibration check flags cov90 outside [{lo:.2f}, "
            f"{hi:.2f}] over {days} scored days: {parts}.", ""]


def write_live_report():
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
        days = ev["origin"].dt.date.nunique()
        lines += [
            f"Forecast days scored: {days}. Resolved rows: {len(ev)}. "
            f"Pending (logged, outcome not yet observed): "
            f"{max(0, len(fc) - len(ev))}.",
            "",
            "Every row here was committed to git before its target hour "
            "completed, so before its outcome was observable; the commit "
            "history is the timestamp evidence.",
            "",
            g.round(4).sort_values("pinball_mean").to_markdown(), "",
        ]
        lines += calibration_lines(g, days)
    path = RESULTS_DIR / "LIVE.md"
    path.write_text("\n".join(lines) + "\n")
    return path
