import numpy as np
import pandas as pd
import pytest

import fbench.models.persistence  # noqa: F401  (registers baselines only)
from fbench import daily
from fbench.features import build_features


@pytest.fixture
def logs_in_tmp(tmp_path, monkeypatch):
    monkeypatch.setattr(daily, "FORECAST_LOG", tmp_path / "forecasts.csv")
    monkeypatch.setattr(daily, "EVAL_LOG", tmp_path / "evaluation.csv")
    monkeypatch.setattr(daily, "RESULTS_DIR", tmp_path)
    return tmp_path


def _frame(n=24 * 400, seed=3):
    idx = pd.date_range("2025-01-01", periods=n, freq="h", tz="UTC")
    rng = np.random.default_rng(seed)
    lr = pd.Series(rng.normal(0, 0.3, n), index=idx).rolling(3).mean()
    return pd.DataFrame({"log_rv": lr, "rv": np.exp(lr)}, index=idx)


def test_log_forecasts_is_idempotent_per_origin(logs_in_tmp):
    h = _frame()
    feats = build_features(h)
    origin = h.index[-30]  # leave future hours unobserved
    first = daily.log_forecasts(feats, origin)
    assert first > 0
    again = daily.log_forecasts(feats, origin)
    assert again == 0


def test_score_due_resolves_only_observed_hours(logs_in_tmp):
    h = _frame()
    feats = build_features(h)
    origin = h.index[-13]  # only 12 of 24 target hours observed
    daily.log_forecasts(feats, origin)
    n_models = len(pd.read_csv(daily.FORECAST_LOG)["model"].unique())
    resolved = daily.score_due(h)
    assert resolved == 12 * n_models
    assert daily.score_due(h) == 0  # second pass appends nothing


def test_live_report_written(logs_in_tmp):
    h = _frame()
    feats = build_features(h)
    daily.log_forecasts(feats, h.index[-25])
    daily.score_due(h)
    path = daily.write_live_report()
    text = path.read_text()
    assert "persistence" in text and "pinball" in text
    # one scored day -> the calibration check must be gated, not verdicted
    assert "Calibration check: inactive" in text


def _per_model(cov90s):
    return pd.DataFrame({"cov90": pd.Series(cov90s)})


def test_calibration_gated_below_min_days():
    lines = daily.calibration_lines(_per_model({"persistence": 1.0}), 3)
    assert "inactive" in lines[0]
    assert "3 so far" in lines[0]


def test_calibration_in_band_with_enough_days():
    lines = daily.calibration_lines(_per_model({"persistence": 0.90}), 12)
    assert "all models inside" in lines[0]


def test_calibration_flags_out_of_band_models():
    lines = daily.calibration_lines(
        _per_model({"a": 0.99, "b": 0.90, "c": 0.79}), 12)
    assert "a 0.9900" in lines[0] and "c 0.7900" in lines[0]
    assert "b 0." not in lines[0]
