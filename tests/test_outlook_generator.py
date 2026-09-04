import numpy as np
import pandas as pd
import pytest

import fbench.models.persistence_model  # noqa: F401  (registers baselines)
from fbench import live_loop, outlook_generator
from fbench.feature_builder import build_features


def test_prob_above_interpolates_and_clamps():
    q = np.array([0.10, 0.20, 0.30, 0.40, 0.50])  # vol-unit quantiles
    assert outlook_generator.prob_above(q, 0.30) == pytest.approx(0.50)
    assert outlook_generator.prob_above(q, 0.05) == pytest.approx(0.98)
    assert outlook_generator.prob_above(q, 0.90) == pytest.approx(0.02)
    # monotone: higher threshold, lower exceedance probability
    ps = [outlook_generator.prob_above(q, t) for t in np.linspace(0.05, 0.6, 12)]
    assert all(a >= b for a, b in zip(ps, ps[1:]))


def test_outlook_written_with_regime_words(tmp_path, monkeypatch):
    monkeypatch.setattr(live_loop, "FORECAST_LOG", tmp_path / "forecasts.csv")
    monkeypatch.setattr(live_loop, "EVAL_LOG", tmp_path / "evaluation.csv")
    monkeypatch.setattr(live_loop, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr(outlook_generator, "FORECAST_LOG", live_loop.FORECAST_LOG)
    monkeypatch.setattr(outlook_generator, "EVAL_LOG", live_loop.EVAL_LOG)
    monkeypatch.setattr(outlook_generator, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr(outlook_generator, "FALLBACK_MODEL", "persistence")

    idx = pd.date_range("2025-01-01", periods=24 * 400, freq="h", tz="UTC")
    rng = np.random.default_rng(5)
    lr = pd.Series(rng.normal(-1, 0.3, len(idx)), index=idx).rolling(3).mean()
    h = pd.DataFrame({"log_rv": lr, "rv": np.exp(lr)}, index=idx)

    live_loop.log_forecasts(build_features(h), h.index[-25])
    path = outlook_generator.write_outlook(h)
    text = path.read_text()
    assert "Volatility outlook" in text
    assert any(
        f"look {w}" in text for w in ("quiet", "normal", "elevated", "high")
    )
    assert "price direction" in text
    # plain-terms translation: present without dollars when no price given
    assert "typical hour is expected to move" in text
    assert "$" not in text
    # with a price, the same layer adds dollar translations of the moves
    text2 = outlook_generator.write_outlook(h, last_price=50_000.0).read_text()
    assert "$50,000" in text2
