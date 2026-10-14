import itertools

import numpy as np
import pandas as pd
import pytest

import fbench.models.persistence_model  # noqa: F401  (registers baselines)
from fbench import daily_forecast_generator, daily_run
from fbench.feature_builder import build_features


def test_prob_above_interpolates_and_clamps():
    quantiles = np.array([0.10, 0.20, 0.30, 0.40, 0.50])  # vol-unit quantiles
    prob_above = daily_forecast_generator.prob_above
    assert prob_above(quantiles, 0.30) == pytest.approx(0.50)
    assert prob_above(quantiles, 0.05) == pytest.approx(0.98)
    assert prob_above(quantiles, 0.90) == pytest.approx(0.02)
    # monotone: higher threshold, lower exceedance probability
    probabilities = [prob_above(quantiles, threshold)
                     for threshold in np.linspace(0.05, 0.6, 12)]
    assert all(lower >= higher
               for lower, higher in itertools.pairwise(probabilities))


def test_quiet_line_sentence_never_prints_equal_numbers_as_above():
    sentence = daily_forecast_generator._quiet_line_sentence
    assert "was 45%, above the 30% quiet line" in sentence(0.45, 0.30)
    assert "was 22%, below the 30% quiet line" in sentence(0.22, 0.30)
    assert "quiet day by that line" in sentence(0.22, 0.30)
    # both round to 30%: a decimal place shows the real gap
    assert "was 30.4%, above the 29.6% quiet line" in sentence(0.304, 0.296)
    assert "was 29.8%, below the 30.2% quiet line" in sentence(0.298, 0.302)
    # an exact tie is at the line, and counts as not quiet
    tie = sentence(0.30, 0.30)
    assert "was 30.00%, at the 30.00% quiet line" in tie
    assert "not a quiet day" in tie
    # a gap too small to print is a tie too, never "at the line, so quiet"
    assert "not a quiet day" in sentence(0.300001, 0.300004)


def test_distinct_percents_adds_places_only_when_the_two_print_alike():
    distinct = daily_forecast_generator.distinct_percents
    assert distinct(0.45, 0.30) == ("45%", "30%", False)
    assert distinct(0.0154, 0.0146, places=1) == ("1.54%", "1.46%", False)
    assert distinct(0.015, 0.006, places=1) == ("1.5%", "0.6%", False)
    assert distinct(0.30, 0.30) == ("30.00%", "30.00%", True)


def test_daily_forecast_written_with_regime_words(tmp_path, monkeypatch):
    monkeypatch.setattr(daily_run, "FORECAST_LOG", tmp_path / "forecasts.csv")
    monkeypatch.setattr(daily_run, "EVAL_LOG", tmp_path / "evaluation.csv")
    monkeypatch.setattr(daily_run, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr(daily_forecast_generator, "FORECAST_LOG", daily_run.FORECAST_LOG)
    monkeypatch.setattr(daily_forecast_generator, "EVAL_LOG", daily_run.EVAL_LOG)
    monkeypatch.setattr(daily_forecast_generator, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr(daily_forecast_generator, "FALLBACK_MODEL", "persistence")

    timestamps = pd.date_range("2025-01-01", periods=24 * 400, freq="h", tz="UTC")
    random_generator = np.random.default_rng(5)
    log_realized_vol = pd.Series(random_generator.normal(-1, 0.3, len(timestamps)),
                                 index=timestamps).rolling(3).mean()
    hourly = pd.DataFrame({"log_rv": log_realized_vol, "rv": np.exp(log_realized_vol)},
                          index=timestamps)

    daily_run.log_forecasts(build_features(hourly), hourly.index[-25])
    path = daily_forecast_generator.write_daily_forecast(hourly)
    text = path.read_text()
    assert "Volatility forecast" in text
    assert any(
        f"look {word}" in text for word in ("quiet", "normal", "elevated", "high")
    )
    assert "price direction" in text
    # plain-terms translation: present without dollars when no price given
    assert "typical hour is expected to move" in text
    assert "$" not in text
    # with a price, the same layer adds dollar translations of the moves
    text_with_price = daily_forecast_generator.write_daily_forecast(
        hourly, last_price=50_000.0).read_text()
    assert "$50,000" in text_with_price


def test_ordinal_suffixes_including_the_teens():
    ordinal = daily_forecast_generator.ordinal
    expected = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th", 11: "11th", 12: "12th",
                13: "13th", 21: "21st", 31: "31st", 42: "42nd", 53: "53rd",
                100: "100th", 101: "101st", 111: "111th"}
    for number, text in expected.items():
        assert ordinal(number) == text
