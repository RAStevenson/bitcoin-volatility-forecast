import numpy as np
import pandas as pd

import fbench.models.persistence  # noqa: F401  (registers baselines)
from fbench import daily, review
from fbench.features import build_features


def _resolved_logs(tmp_path, monkeypatch, shock=1.0):
    monkeypatch.setattr(daily, "FORECAST_LOG", tmp_path / "forecasts.csv")
    monkeypatch.setattr(daily, "EVAL_LOG", tmp_path / "evaluation.csv")
    monkeypatch.setattr(daily, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr(review, "EVAL_LOG", daily.EVAL_LOG)
    monkeypatch.setattr(review, "RESULTS_DIR", tmp_path)

    idx = pd.date_range("2025-01-01", periods=24 * 400, freq="h", tz="UTC")
    rng = np.random.default_rng(5)
    lr = pd.Series(rng.normal(-1, 0.3, len(idx)), index=idx).rolling(3).mean()
    h = pd.DataFrame({"log_rv": lr, "rv": np.exp(lr)}, index=idx)
    origin = h.index[-25]
    daily.log_forecasts(build_features(h), origin)
    # The forecast is fit on data to origin; the actuals for the 24 target
    # hours are then scaled so the test controls how wrong it was.
    h.loc[h.index > origin, "log_rv"] += np.log(shock)
    daily.score_due(h)
    return h


def test_review_on_target_for_ordinary_day(tmp_path, monkeypatch):
    _resolved_logs(tmp_path, monkeypatch)
    text = review.write_review().read_text()
    assert "Yesterday in review" in text
    assert "on target" in text
    assert "price direction" in text


def test_review_calls_a_large_miss_too_low(tmp_path, monkeypatch):
    _resolved_logs(tmp_path, monkeypatch, shock=4.0)
    text = review.write_review().read_text()
    assert "too low" in text
    assert "worst of 1 scored days" in text


def test_review_needs_no_resolved_rows(tmp_path, monkeypatch):
    monkeypatch.setattr(review, "EVAL_LOG", tmp_path / "missing.csv")
    assert "No resolved forecasts yet" in review.build_review()
