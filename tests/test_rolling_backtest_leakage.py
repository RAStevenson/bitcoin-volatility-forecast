import numpy as np
import pandas as pd

from fbench.feature_builder import build_features
from fbench.models.har_model import Har
from fbench.models.persistence_model import Persistence
from fbench.rolling_backtest import make_origins, run_backtest


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
