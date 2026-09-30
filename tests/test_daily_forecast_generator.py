import numpy as np
import pandas as pd
import pytest

import fbench.models.persistence_model  # noqa: F401  (registers baselines)
from fbench import daily_run, daily_forecast_generator
from fbench.feature_builder import build_features


def test_prob_above_interpolates_and_clamps():
    q = np.array([0.10, 0.20, 0.30, 0.40, 0.50])  # vol-unit quantiles
    assert daily_forecast_generator.prob_above(q, 0.30) == pytest.approx(0.50)
    assert daily_forecast_generator.prob_above(q, 0.05) == pytest.approx(0.98)
    assert daily_forecast_generator.prob_above(q, 0.90) == pytest.approx(0.02)
    # monotone: higher threshold, lower exceedance probability
    ps = [daily_forecast_generator.prob_above(q, t) for t in np.linspace(0.05, 0.6, 12)]
    assert all(a >= b for a, b in zip(ps, ps[1:]))


def test_quiet_line_sentence_never_prints_equal_numbers_as_above():
    s = daily_forecast_generator._quiet_line_sentence
    assert "was 45%, above the 30% quiet line" in s(0.45, 0.30)
    assert "was 22%, below the 30% quiet line" in s(0.22, 0.30)
    assert "quiet day by that line" in s(0.22, 0.30)
    # both round to 30%: a decimal place shows the real gap
    assert "was 30.4%, above the 29.6% quiet line" in s(0.304, 0.296)
    assert "was 29.8%, below the 30.2% quiet line" in s(0.298, 0.302)
    # an exact tie is at the line, and counts as not quiet
    tie = s(0.30, 0.30)
    assert "was 30.00%, at the 30.00% quiet line" in tie
    assert "not a quiet day" in tie
    # a gap too small to print is a tie too, never "at the line, so quiet"
    assert "not a quiet day" in s(0.300001, 0.300004)


def test_distinct_percents_adds_places_only_when_the_two_print_alike():
    d = daily_forecast_generator.distinct_percents
    assert d(0.45, 0.30) == ("45%", "30%", False)
    assert d(0.0154, 0.0146, places=1) == ("1.54%", "1.46%", False)
    assert d(0.015, 0.006, places=1) == ("1.5%", "0.6%", False)
    assert d(0.30, 0.30) == ("30.00%", "30.00%", True)


def test_daily_forecast_written_with_regime_words(tmp_path, monkeypatch):
    monkeypatch.setattr(daily_run, "FORECAST_LOG", tmp_path / "forecasts.csv")
    monkeypatch.setattr(daily_run, "EVAL_LOG", tmp_path / "evaluation.csv")
    monkeypatch.setattr(daily_run, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr(daily_forecast_generator, "FORECAST_LOG", daily_run.FORECAST_LOG)
    monkeypatch.setattr(daily_forecast_generator, "EVAL_LOG", daily_run.EVAL_LOG)
    monkeypatch.setattr(daily_forecast_generator, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr(daily_forecast_generator, "FALLBACK_MODEL", "persistence")

    idx = pd.date_range("2025-01-01", periods=24 * 400, freq="h", tz="UTC")
    rng = np.random.default_rng(5)
    lr = pd.Series(rng.normal(-1, 0.3, len(idx)), index=idx).rolling(3).mean()
    h = pd.DataFrame({"log_rv": lr, "rv": np.exp(lr)}, index=idx)

    daily_run.log_forecasts(build_features(h), h.index[-25])
    path = daily_forecast_generator.write_daily_forecast(h)
    text = path.read_text()
    assert "Volatility forecast" in text
    assert any(
        f"look {w}" in text for w in ("quiet", "normal", "elevated", "high")
    )
    assert "price direction" in text
    # plain-terms translation: present without dollars when no price given
    assert "typical hour is expected to move" in text
    assert "$" not in text
    # with a price, the same layer adds dollar translations of the moves
    text2 = daily_forecast_generator.write_daily_forecast(h, last_price=50_000.0).read_text()
    assert "$50,000" in text2
