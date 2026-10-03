import numpy as np
import pandas as pd

from fbench.feature_builder import build_features
from fbench.models.persistence_model import Persistence
from fbench.rolling_backtest import make_origins, run_backtest


def test_engine_never_shows_future_to_models(monkeypatch):
    """The engine hands each model only rows up to its forecast origin.
    Persistence's fit is wrapped to note the last timestamp it was given
    at each origin, and every one must be at or before that origin."""
    idx = pd.date_range("2025-01-01", periods=24 * 200, freq="h", tz="UTC")
    rng = np.random.default_rng(0)
    feats = build_features(
        pd.DataFrame({"log_rv": rng.normal(size=len(idx))}, index=idx))
    origins = make_origins(feats.index, test_days=20, stride_days=5)
    last_seen = []
    original_fit = Persistence.fit

    def noting_fit(self, train):
        last_seen.append(train.index.max())
        return original_fit(self, train)

    monkeypatch.setattr(Persistence, "fit", noting_fit)
    res = run_backtest(feats, ["persistence"], origins)
    assert len(last_seen) == len(origins)
    for origin, seen in zip(origins, last_seen, strict=True):
        assert seen <= origin
    assert (res["target_time"] > res["origin"]).all()
