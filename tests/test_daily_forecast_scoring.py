import numpy as np
import pandas as pd

import bitcoin_volatility_forecast.models.persistence_model  # noqa: F401  (registers baselines)
from bitcoin_volatility_forecast import (
    daily_forecast_generator,
    daily_forecast_scoring,
    daily_run,
    review_generator,
)
from bitcoin_volatility_forecast.feature_builder import build_features
from bitcoin_volatility_forecast.forecast_settings import HORIZON


def _hourly(n_hours=24 * 400, seed=5, with_close=True):
    timestamps = pd.date_range("2025-01-01", periods=n_hours, freq="h", tz="UTC")
    random_generator = np.random.default_rng(seed)
    log_realized_vol = pd.Series(random_generator.normal(-1, 0.3, n_hours),
                                 index=timestamps).rolling(3).mean()
    hourly = pd.DataFrame({"log_rv": log_realized_vol, "rv": np.exp(log_realized_vol)},
                          index=timestamps)
    if with_close:
        hourly["close"] = 100.0 * np.exp(
            random_generator.normal(0, 0.001, n_hours).cumsum())
    return hourly


def test_claims_and_realized_agree_when_the_median_is_exact():
    hourly = _hourly()
    origin = hourly.index[-25]
    comparison_context = daily_forecast_generator.context(hourly["rv"].loc[:origin])
    target_hours = pd.date_range(origin + pd.Timedelta(hours=1), periods=HORIZON,
                                 freq="h", tz="UTC")
    shuffled_positions = np.random.default_rng(1).permutation(HORIZON)
    median = np.linspace(0.3, 0.6, HORIZON)[shuffled_positions]
    annualized_quantiles = np.column_stack([median * 0.6, median * 0.8, median,
                                            median * 1.2, median * 1.6])
    forecast_claims = daily_forecast_generator.claims(annualized_quantiles, target_hours,
                                                      comparison_context)
    realized_day_claims = daily_forecast_generator.realized_claims(
        pd.Series(median, index=target_hours), comparison_context)
    assert forecast_claims["regime"] == realized_day_claims["regime"]
    assert forecast_claims["trend"] == realized_day_claims["trend"]
    assert set(forecast_claims["loud"]) == set(realized_day_claims["loud"])
    assert set(forecast_claims["calm"]) == set(realized_day_claims["calm"])
    assert forecast_claims["regime"] in daily_forecast_generator.REGIMES


def _one_day_log(hourly, origin, end_price):
    """Evaluation log with one model over one origin, whose median
    forecast equals what realized, and a close series pinned at the two
    ends the day-move claim is measured between."""
    target_hours = pd.date_range(origin + pd.Timedelta(hours=1), periods=HORIZON,
                                 freq="h", tz="UTC")
    log_realized_vol = hourly["log_rv"].reindex(target_hours).to_numpy()
    evaluations = pd.DataFrame({
        "origin": origin, "target_time": target_hours,
        "horizon": range(1, HORIZON + 1), "model": "persistence",
        "q05": log_realized_vol - 0.5, "q25": log_realized_vol - 0.2,
        "q50": log_realized_vol, "q75": log_realized_vol + 0.2,
        "q95": log_realized_vol + 0.5, "y_true": log_realized_vol})
    hourly = hourly.copy()
    hourly.loc[origin, "close"] = 100.0
    hourly.loc[origin + pd.Timedelta(hours=HORIZON), "close"] = end_price
    return evaluations, hourly


def test_day_move_hit_is_close_to_close():
    hourly = _hourly()
    origin = hourly.index[-25]
    evaluations, hourly_inside = _one_day_log(hourly, origin, end_price=100.0)
    scored = daily_forecast_scoring.score_daily_forecast(evaluations, hourly_inside)
    assert len(scored) == 1
    day_move = float(scored["day_move"].iloc[0])
    assert 0 < day_move < 0.2
    assert bool(scored["day_move_hit"].iloc[0]) is True
    # a day that moved twice the stated distance is a miss
    evaluations, hourly_outside = _one_day_log(hourly, origin,
                                               end_price=100.0 * (1 + 2 * day_move))
    scored = daily_forecast_scoring.score_daily_forecast(evaluations, hourly_outside)
    assert bool(scored["day_move_hit"].iloc[0]) is False
    # the exact-median day matches on every word and names every hour
    assert scored["regime_gap"].iloc[0] == 0
    assert scored["trend_forecast"].iloc[0] == scored["trend_realized"].iloc[0]
    assert scored["loud_overlap"].iloc[0] == 3
    assert scored["calm_overlap"].iloc[0] == 3
    # the yesterday baseline is scored on the same day in the same terms
    for column in ("yesterday_regime_hit", "yesterday_trend_hit", "yesterday_day_move_hit"):
        assert scored[column].iloc[0] in (True, False)
    assert 0 <= scored["yesterday_loud_overlap"].iloc[0] <= 3
    assert scored["yesterday_high_hours"].iloc[0] >= 0


def test_day_move_is_skipped_without_close():
    hourly = _hourly(with_close=False)
    origin = hourly.index[-25]
    evaluations, _ = _one_day_log(_hourly(), origin, end_price=100.0)
    scored = daily_forecast_scoring.score_daily_forecast(evaluations, hourly)
    assert scored["day_return"].iloc[0] is None
    lines = daily_forecast_scoring.record_lines(scored)
    assert not any("one-standard-deviation" in line for line in lines)
    assert any("regime word" in line for line in lines)
    assert any("Repeating yesterday's word" in line for line in lines)


def test_partially_resolved_day_is_not_scored():
    hourly = _hourly()
    origin = hourly.index[-25]
    evaluations, hourly_inside = _one_day_log(hourly, origin, end_price=100.0)
    assert daily_forecast_scoring.score_daily_forecast(evaluations.iloc[:-1],
                                                       hourly_inside).empty


def test_review_carries_the_daily_forecast_record(tmp_path, monkeypatch):
    monkeypatch.setattr(daily_run, "FORECAST_LOG", tmp_path / "forecasts.csv")
    monkeypatch.setattr(daily_run, "EVAL_LOG", tmp_path / "evaluation.csv")
    monkeypatch.setattr(daily_run, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr(review_generator, "EVAL_LOG", daily_run.EVAL_LOG)
    monkeypatch.setattr(review_generator, "RESULTS_DIR", tmp_path)
    hourly = _hourly()
    origin = hourly.index[-25]
    daily_run.log_forecasts(build_features(hourly), origin)
    daily_run.score_due(hourly)
    text = review_generator.write_review(hourly).read_text()
    assert "The daily forecast's own claims" in text
    assert "Over 1 resolved days" in text
    assert "one-standard-deviation day move on" in text
    # without the hourly series the section is omitted, not faked
    assert "daily forecast's own claims" not in review_generator.build_review()
