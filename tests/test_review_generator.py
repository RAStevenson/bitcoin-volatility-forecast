import numpy as np
import pandas as pd

import fbench.models.persistence_model  # noqa: F401  (registers baselines)
from fbench import daily_run, review_generator
from fbench.feature_builder import build_features


def _resolved_logs(tmp_path, monkeypatch, shock=1.0):
    monkeypatch.setattr(daily_run, "FORECAST_LOG", tmp_path / "forecasts.csv")
    monkeypatch.setattr(daily_run, "EVAL_LOG", tmp_path / "evaluation.csv")
    monkeypatch.setattr(daily_run, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr(review_generator, "EVAL_LOG", daily_run.EVAL_LOG)
    monkeypatch.setattr(review_generator, "RESULTS_DIR", tmp_path)

    idx = pd.date_range("2025-01-01", periods=24 * 400, freq="h", tz="UTC")
    rng = np.random.default_rng(5)
    log_realized_vol = pd.Series(rng.normal(-1, 0.3, len(idx)), index=idx).rolling(3).mean()
    hourly = pd.DataFrame({"log_rv": log_realized_vol, "rv": np.exp(log_realized_vol)},
                          index=idx)
    origin = hourly.index[-25]
    daily_run.log_forecasts(build_features(hourly), origin)
    # The forecast is fit on data to origin; the actuals for the 24 target
    # hours are then scaled so the test controls how wrong it was.
    hourly.loc[hourly.index > origin, "log_rv"] += np.log(shock)
    daily_run.score_due(hourly)
    return hourly


def test_review_on_target_for_ordinary_day(tmp_path, monkeypatch):
    _resolved_logs(tmp_path, monkeypatch)
    text = review_generator.write_review().read_text()
    assert "Yesterday in review" in text
    assert "on target" in text
    assert "price direction" in text


def test_review_calls_a_large_miss_too_low(tmp_path, monkeypatch):
    _resolved_logs(tmp_path, monkeypatch, shock=4.0)
    text = review_generator.write_review().read_text()
    assert "too low" in text
    assert "this was the only scored day so far" in text


def test_rank_is_counted_from_the_nearer_end():
    phrase = review_generator._rank_phrase
    # the lowest error of 57: 57 days are at least as bad, 1 at most as bad
    assert phrase(57, 1, 57) == "best of 57 scored days"
    assert phrase(55, 3, 57) == "3rd best of 57 scored days"
    assert phrase(1, 57, 57) == "worst of 57 scored days"
    assert phrase(2, 56, 57) == "2nd worst of 57 scored days"
    assert phrase(29, 29, 57) == "middle day of 57 scored days"


def test_review_needs_no_resolved_rows(tmp_path, monkeypatch):
    monkeypatch.setattr(review_generator, "EVAL_LOG", tmp_path / "missing.csv")
    assert "No resolved forecasts yet" in review_generator.build_review()
