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


def test_day_path_switches_rule_at_the_release_origin(monkeypatch):
    monkeypatch.setattr(daily_forecast_generator, "RELEASE_ORIGIN", "2026-03-01 10:00")
    sigma = daily_run.IQR_TO_SIGMA
    log_quantiles = np.tile([-1.6, -1 - sigma / 2, -1.0, -1 + sigma / 2, -0.4], (24, 1))
    annualized_quantiles = np.exp(log_quantiles)
    before = pd.date_range("2026-02-28 11:00", periods=24, freq="h", tz="UTC")
    after = pd.date_range("2026-03-01 11:00", periods=24, freq="h", tz="UTC")
    # before the release the day figure is the median path
    np.testing.assert_allclose(daily_forecast_generator.day_path(annualized_quantiles, before),
                               np.exp(-1.0))
    # from the release on it is the expected value, the median times exp(1/2) here
    np.testing.assert_allclose(daily_forecast_generator.day_path(annualized_quantiles, after),
                               np.exp(-0.5))
    # the typical-hour move stays on the medians under either rule, while
    # the day figure follows the rule in force
    comparison_context = {"daily_averages": np.linspace(0.1, 0.9, 100),
                          "high_line": 0.67, "previous_day_average": 0.3}
    for target_times, expected_average in ((before, np.exp(-1.0)), (after, np.exp(-0.5))):
        forecast_claims = daily_forecast_generator.claims(annualized_quantiles, target_times,
                                                          comparison_context)
        assert forecast_claims["forecast_average"] == pytest.approx(expected_average)
        assert forecast_claims["hourly_move"] == pytest.approx(
            np.exp(-1.0) / daily_forecast_generator.ANNUALIZER)
    assert not daily_forecast_generator.uses_expected_value(before)
    assert daily_forecast_generator.uses_expected_value(after)


def test_ordinal_suffixes_including_the_teens():
    ordinal = daily_forecast_generator.ordinal
    expected = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th", 11: "11th", 12: "12th",
                13: "13th", 21: "21st", 31: "31st", 42: "42nd", 53: "53rd",
                100: "100th", 101: "101st", 111: "111th"}
    for number, text in expected.items():
        assert ordinal(number) == text


def _high_hours_claims(q95_by_hour, high_line=0.67):
    """Claims from 24 hours whose bands all sit at 0.20 to 0.30 except for
    the 95% quantile, set per hour, so only the top of each band decides
    its chance of running above the high line."""
    quantiles = np.tile([0.20, 0.25, 0.27, 0.30, 0.30], (24, 1)).astype(float)
    quantiles[:, 4] = q95_by_hour
    target_hours = pd.date_range("2026-01-02 11:00", periods=24, freq="h", tz="UTC")
    comparison_context = {"daily_averages": np.linspace(0.1, 0.9, 100),
                          "high_line": high_line, "previous_day_average": 0.3}
    return daily_forecast_generator.claims(quantiles, target_hours, comparison_context)


def test_high_hours_count_prints_only_when_it_clears_the_probability_floor():
    floor = daily_forecast_generator.PROBABILITY_FLOOR
    # every band below the line: the sum is the floor alone, 24 x 0.02
    at_floor = _high_hours_claims(np.full(24, 0.30))
    assert at_floor["expected_high_hours"] == pytest.approx(24 * floor)
    assert at_floor["all_at_floor"] and at_floor["no_meaningful_high"]
    # one band a hair over the line: a count that is still mostly floor
    one_hour = np.full(24, 0.30)
    one_hour[0] = 0.70
    barely = _high_hours_claims(one_hour)
    assert not barely["all_at_floor"]
    assert barely["expected_high_hours"] - 24 * floor < 0.5
    assert barely["no_meaningful_high"]
    # six bands with real mass above the line: a count worth printing
    six_hours = np.full(24, 0.30)
    six_hours[:6] = 2.0
    meaningful = _high_hours_claims(six_hours)
    assert meaningful["expected_high_hours"] - 24 * floor >= 0.5
    assert not meaningful["no_meaningful_high"]
