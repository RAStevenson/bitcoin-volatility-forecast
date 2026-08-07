import numpy as np
import pandas as pd
import pytest

import fbench.models.persistence  # noqa: F401  (registers baselines)
from fbench import daily, outlook
from fbench.features import build_features


def test_prob_above_interpolates_and_clamps():
    q = np.array([0.10, 0.20, 0.30, 0.40, 0.50])  # vol-unit quantiles
    assert outlook.prob_above(q, 0.30) == pytest.approx(0.50)
    assert outlook.prob_above(q, 0.05) == pytest.approx(0.98)
    assert outlook.prob_above(q, 0.90) == pytest.approx(0.02)
    # monotone: higher threshold, lower exceedance probability
    ps = [outlook.prob_above(q, t) for t in np.linspace(0.05, 0.6, 12)]
    assert all(a >= b for a, b in zip(ps, ps[1:]))


def test_outlook_written_with_regime_words(tmp_path, monkeypatch):
    monkeypatch.setattr(daily, "FORECAST_LOG", tmp_path / "forecasts.csv")
    monkeypatch.setattr(daily, "EVAL_LOG", tmp_path / "evaluation.csv")
    monkeypatch.setattr(daily, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr(outlook, "FORECAST_LOG", daily.FORECAST_LOG)
    monkeypatch.setattr(outlook, "EVAL_LOG", daily.EVAL_LOG)
    monkeypatch.setattr(outlook, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr(outlook, "FALLBACK_MODEL", "persistence")

    idx = pd.date_range("2025-01-01", periods=24 * 400, freq="h", tz="UTC")
    rng = np.random.default_rng(5)
    lr = pd.Series(rng.normal(-1, 0.3, len(idx)), index=idx).rolling(3).mean()
    h = pd.DataFrame({"log_rv": lr, "rv": np.exp(lr)}, index=idx)

    daily.log_forecasts(build_features(h), h.index[-25])
    path = outlook.write_outlook(h)
    text = path.read_text()
    assert "Volatility outlook" in text
    assert any(
        f"look {w}" in text for w in ("quiet", "normal", "elevated", "high")
    )
    assert "price direction" in text
