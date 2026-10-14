import numpy as np
import pandas as pd

import fbench.models.persistence_model  # noqa: F401  (registers baselines)
from fbench import daily_run, review_generator
from fbench.feature_builder import build_features


def _resolved_logs(tmp_path, monkeypatch, realized_multiplier=1.0):
    monkeypatch.setattr(daily_run, "FORECAST_LOG", tmp_path / "forecasts.csv")
    monkeypatch.setattr(daily_run, "EVAL_LOG", tmp_path / "evaluation.csv")
    monkeypatch.setattr(daily_run, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr(review_generator, "EVAL_LOG", daily_run.EVAL_LOG)
    monkeypatch.setattr(review_generator, "RESULTS_DIR", tmp_path)

    timestamps = pd.date_range("2025-01-01", periods=24 * 400, freq="h", tz="UTC")
    random_generator = np.random.default_rng(5)
    log_realized_vol = pd.Series(random_generator.normal(-1, 0.3, len(timestamps)),
                                 index=timestamps).rolling(3).mean()
    hourly = pd.DataFrame({"log_rv": log_realized_vol, "rv": np.exp(log_realized_vol)},
                          index=timestamps)
    origin = hourly.index[-25]
    daily_run.log_forecasts(build_features(hourly), origin)
    # The forecast is fit on data to origin; the actuals for the 24 target
    # hours are then scaled so the test controls how wrong it was.
    hourly.loc[hourly.index > origin, "log_rv"] += np.log(realized_multiplier)
    daily_run.score_due(hourly)
    return hourly


def test_review_on_target_for_ordinary_day(tmp_path, monkeypatch):
    _resolved_logs(tmp_path, monkeypatch)
    text = review_generator.write_review().read_text()
    assert "Yesterday in review" in text
    assert "on target" in text
    assert "price direction" in text


def test_review_calls_a_large_miss_too_low(tmp_path, monkeypatch):
    _resolved_logs(tmp_path, monkeypatch, realized_multiplier=4.0)
    text = review_generator.write_review().read_text()
    assert "too low" in text
    assert "with no other scored day to rank it against" in text


def test_rank_is_counted_from_the_nearer_end():
    phrase = review_generator._rank_phrase
    # the lowest error of 57: 57 days are at least as large, 1 at most
    assert phrase(57, 1, 57) == "the smallest of 57 scored days"
    assert phrase(55, 3, 57) == "the 3rd smallest of 57 scored days"
    assert phrase(1, 57, 57) == "the largest of 57 scored days"
    assert phrase(2, 56, 57) == "the 2nd largest of 57 scored days"
    # the edge of the outer thirds: ceil(57 / 3) = 19 is still counted
    assert phrase(19, 39, 57) == "the 19th largest of 57 scored days"
    assert phrase(39, 19, 57) == "the 19th smallest of 57 scored days"


def test_rank_names_the_middle_third_instead_of_a_place():
    phrase = review_generator._rank_phrase
    assert phrase(20, 38, 57) == "in the middle third of 57 scored days"
    assert phrase(29, 29, 57) == "in the middle third of 57 scored days"
    assert phrase(28, 43, 70) == "in the middle third of 70 scored days"
    # two days have no middle third; three have one, the middle day
    assert phrase(1, 2, 2) == "the largest of 2 scored days"
    assert phrase(2, 1, 2) == "the smallest of 2 scored days"
    assert phrase(2, 2, 3) == "in the middle third of 3 scored days"
    assert phrase(1, 1, 1) == "with no other scored day to rank it against"
    # a day equally far from both ends outside the middle third is a tie
    assert phrase(2, 2, 4) == "at the median of 4 scored days"
    assert phrase(1, 1, 2) == "at the median of 2 scored days"


def test_review_needs_no_resolved_rows(tmp_path, monkeypatch):
    monkeypatch.setattr(review_generator, "EVAL_LOG", tmp_path / "missing.csv")
    assert "No resolved forecasts yet" in review_generator.build_review()
