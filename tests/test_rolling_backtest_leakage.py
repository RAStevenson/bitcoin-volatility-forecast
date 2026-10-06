import numpy as np
import pandas as pd

from fbench.feature_builder import build_features
from fbench.models.persistence_model import Persistence
from fbench.rolling_backtest import make_origins, run_backtest


def test_engine_never_shows_future_to_models(monkeypatch):
    """The engine hands each model only rows up to its forecast origin.
    Persistence's fit is wrapped to note the last timestamp it was given
    at each origin, and every one must be at or before that origin."""
    timestamps = pd.date_range("2025-01-01", periods=24 * 200, freq="h", tz="UTC")
    random_generator = np.random.default_rng(0)
    features = build_features(pd.DataFrame(
        {"log_rv": random_generator.normal(size=len(timestamps))}, index=timestamps))
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
