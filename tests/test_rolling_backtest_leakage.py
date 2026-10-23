import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import bitcoin_volatility_forecast.models.nhits_model
import bitcoin_volatility_forecast.models.prophet_model
import bitcoin_volatility_forecast.models.sarima_model
import bitcoin_volatility_forecast.models.xgboost_model  # noqa: F401  (registers every model)
from bitcoin_volatility_forecast import daily_run
from bitcoin_volatility_forecast.daily_forecast_generator import leading_model_asof
from bitcoin_volatility_forecast.feature_builder import build_features
from bitcoin_volatility_forecast.forecast_settings import HISTORY_START, QCOLS, TRAIN_DAYS
from bitcoin_volatility_forecast.models.base_forecast_model import REGISTRY
from bitcoin_volatility_forecast.models.har_model import Har
from bitcoin_volatility_forecast.models.persistence_model import Persistence
from bitcoin_volatility_forecast.rolling_backtest import check_no_future, make_origins, run_backtest


def _features(seed=0, n_days=200):
    timestamps = pd.date_range("2025-01-01", periods=24 * n_days, freq="h", tz="UTC")
    random_generator = np.random.default_rng(seed)
    hourly = pd.DataFrame({"log_rv": random_generator.normal(size=len(timestamps))},
                          index=timestamps)
    return hourly, build_features(hourly)


def test_engine_never_shows_future_to_models(monkeypatch):
    """The engine hands each model only rows up to its forecast origin.
    Persistence's fit is wrapped to note the last timestamp it was given
    at each origin, and every one must be at or before that origin."""
    _, features = _features()
    origins = make_origins(features.index, test_days=20, stride_days=5)
    last_seen = []
    original_fit = Persistence.fit

    def noting_fit(self, training_rows):
        last_seen.append(training_rows.index.max())
        return original_fit(self, training_rows)

    monkeypatch.setattr(Persistence, "fit", noting_fit)
    forecasts = run_backtest(features, ["persistence"], origins)
    assert len(last_seen) == len(origins)
    for origin, last_seen_time in zip(origins, last_seen, strict=True):
        assert last_seen_time <= origin
    assert (forecasts["target_time"] > forecasts["origin"]).all()


def test_har_uses_the_origin_hour_and_nothing_after_it():
    """HAR's forecast from an origin must use the origin hour's own value
    and must not move when every hour after the origin is rewritten: the
    first is the information the fix put back, the second is the leakage
    rule."""
    hourly, features = _features()
    origin = hourly.index[-30]
    future = pd.date_range(origin + pd.Timedelta(hours=1), periods=24, freq="h", tz="UTC")
    model = Har()
    model.fit(features.loc[:origin])
    assert model.origin_features_[0] == hourly.loc[origin, "log_rv"]
    forecast = model.predict(future)

    rewritten = hourly.copy()
    rewritten.loc[rewritten.index > origin, "log_rv"] = 999.0
    refit = Har()
    refit.fit(build_features(rewritten).loc[:origin])
    pd.testing.assert_frame_equal(refit.predict(future), forecast)

    # and the origin hour itself matters: changing it changes the forecast
    moved = hourly.copy()
    moved.loc[origin, "log_rv"] += 1.0
    refit_moved = Har()
    refit_moved.fit(build_features(moved).loc[:origin])
    assert not refit_moved.predict(future).equals(forecast)


def test_make_origins_sit_at_the_requested_hour():
    _, features = _features()
    midnight_origins = make_origins(features.index, test_days=20, stride_days=5)
    assert set(midnight_origins.hour) == {0}
    ten_utc_origins = make_origins(features.index, test_days=20, stride_days=5,
                                   origin_hour_utc=10)
    assert set(ten_utc_origins.hour) == {10}
    assert len(ten_utc_origins) == len(midnight_origins)
    # every target of the last origin is inside the series
    assert ten_utc_origins[-1] + pd.Timedelta(hours=24) <= features.index[-1]
    assert (ten_utc_origins - midnight_origins == pd.Timedelta(hours=10)).all()


# The tests below check the leakage rule end to end: for every model, for
# the daily run, for the choice of the reported model, and for the tuning.


def _volatility_series(n_days=70, seed=1):
    """A synthetic hourly log RV series with some persistence, so every
    model has something to fit."""
    timestamps = pd.date_range("2025-01-01", periods=24 * n_days, freq="h", tz="UTC")
    random_generator = np.random.default_rng(seed)
    log_realized_vol = pd.Series(random_generator.normal(-1, 0.3, len(timestamps)),
                                 index=timestamps).rolling(3).mean()
    return pd.DataFrame({"log_rv": log_realized_vol}, index=timestamps)


def _quantiles(forecasts):
    """The five quantile columns of a backtest frame, indexed by model and
    target hour."""
    return forecasts.set_index(["model", "target_time"]).sort_index()[QCOLS]


def test_no_model_sees_past_its_origin():
    """For every registered model, rewriting every hour after the origin
    with an impossible value leaves the forecast from that origin exactly
    unchanged. Moving the origin hour itself changes every model's
    forecast, which shows the test would notice a model that ignored its
    newest hour as well as one that read past it."""
    hourly = _volatility_series()
    origin = hourly.index[-48]
    models = sorted(REGISTRY)
    baseline = _quantiles(run_backtest(build_features(hourly), models, [origin]))

    rewritten = hourly.copy()
    rewritten.loc[rewritten.index > origin, "log_rv"] = 999.0
    pd.testing.assert_frame_equal(
        _quantiles(run_backtest(build_features(rewritten), models, [origin])),
        baseline, check_exact=True)

    moved = hourly.copy()
    moved.loc[origin, "log_rv"] += 1.0
    moved_forecasts = _quantiles(run_backtest(build_features(moved), models, [origin]))
    for model_name in models:
        assert not moved_forecasts.loc[model_name].equals(baseline.loc[model_name]), model_name


def test_a_late_daily_run_logs_the_same_forecast(tmp_path, monkeypatch):
    """The daily run's forecast from its fixed origin is byte for byte the
    same whether the series ends at the origin hour, as on an on-time run,
    or runs on six hours past it, as on a run that starts late."""
    hourly = _volatility_series()
    origin = hourly.index[-48]
    monkeypatch.setattr(daily_run, "RESULTS_DIR", tmp_path)
    logged = []
    for run_name, series in (("on_time", hourly.loc[:origin]),
                             ("late", hourly.loc[:origin + pd.Timedelta(hours=6)])):
        monkeypatch.setattr(daily_run, "FORECAST_LOG", tmp_path / f"{run_name}.csv")
        daily_run.log_forecasts(build_features(series), origin)
        logged.append((tmp_path / f"{run_name}.csv").read_bytes())
    assert logged[0] == logged[1]


def _scored_days(first_origin, n_days, accurate_model, other_model):
    """Fully resolved days on which accurate_model's median is the truth
    and other_model's is a whole log unit off."""
    rows = []
    for day in range(n_days):
        origin = first_origin + pd.Timedelta(days=day)
        for hour in range(24):
            for model_name, offset in ((accurate_model, 0.0), (other_model, 1.0)):
                rows.append({"origin": origin,
                             "target_time": origin + pd.Timedelta(hours=hour + 1),
                             "horizon": hour + 1, "model": model_name,
                             "q05": -1.6 + offset, "q25": -1.25 + offset,
                             "q50": -1.0 + offset, "q75": -0.75 + offset,
                             "q95": -0.4 + offset, "y_true": -1.0})
    return rows


def test_the_reported_leader_is_chosen_from_earlier_days_only():
    """The model a day's report names is the leader on the days scored
    before it. Here the early model leads the first three days and the
    late model the four after, so the late model leads overall, yet the
    fourth day's report must still name the early model."""
    start = pd.Timestamp("2026-01-01 10:00", tz="UTC")
    evaluations = pd.DataFrame(
        _scored_days(start, 3, "early", "late")
        + _scored_days(start + pd.Timedelta(days=3), 4, "late", "early"))
    assert leading_model_asof(evaluations, start + pd.Timedelta(days=3)) == "early"
    assert leading_model_asof(evaluations, start + pd.Timedelta(days=7)) == "late"


def _run_tune_module():
    """scripts/run_tune.py loaded as a module; its main runs only behind
    the __main__ guard, so loading it runs nothing."""
    path = Path(__file__).resolve().parents[1] / "scripts" / "run_tune.py"
    spec = importlib.util.spec_from_file_location("run_tune", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_tuning_never_sees_the_test_year():
    """The tuning script keeps only hours before the test year, and every
    origin it scores has its whole training window after HISTORY_START
    and all 24 target hours before the test year starts."""
    run_tune = _run_tune_module()
    test_year_start = pd.Timestamp(run_tune.TEST_YEAR_START, tz="UTC")
    timestamps = pd.date_range(pd.Timestamp(HISTORY_START, tz="UTC"),
                               test_year_start + pd.Timedelta(days=60), freq="h")
    hourly = pd.DataFrame({"log_rv": np.zeros(len(timestamps))}, index=timestamps)
    tuning_hours = run_tune.tuning_data(hourly)
    assert tuning_hours.index.max() < test_year_start
    origins = run_tune.tuning_origins(build_features(tuning_hours), 5, 10)
    run_tune.check_before_test_year(origins)
    assert origins[-1] + pd.Timedelta(hours=24) < test_year_start
    assert (origins[0] - pd.Timedelta(days=TRAIN_DAYS)
            >= pd.Timestamp(HISTORY_START, tz="UTC"))
    with pytest.raises(ValueError, match="test year"):
        run_tune.check_before_test_year(pd.DatetimeIndex([test_year_start]))


def test_the_leakage_check_raises():
    """The check the backtest and the daily run make before every fit
    raises on a training row past the origin and on a target hour at or
    before it, and stays silent on a correct split."""
    timestamps = pd.date_range("2026-01-01", periods=48, freq="h", tz="UTC")
    rows = pd.DataFrame({"log_rv": 0.0}, index=timestamps)
    origin = timestamps[23]
    targets = pd.date_range(origin + pd.Timedelta(hours=1), periods=24, freq="h", tz="UTC")
    check_no_future(rows.loc[:origin], targets, origin)
    with pytest.raises(ValueError, match="past the origin"):
        check_no_future(rows, targets, origin)
    with pytest.raises(ValueError, match="not after the origin"):
        check_no_future(rows.loc[:origin], targets - pd.Timedelta(hours=1), origin)
