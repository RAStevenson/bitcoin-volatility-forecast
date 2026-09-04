import numpy as np
import pandas as pd

from fbench.rolling_backtest import make_origins, run_backtest
from fbench.feature_builder import build_features
from fbench.models.forecast_model import ForecastModel, quantile_frame, register


@register
class _Spy(ForecastModel):
    name = "_spy"
    train_days = 30
    seen = []

    def fit(self, train):
        _Spy.seen.append(train.index.max())

    def predict(self, index):
        return quantile_frame(np.zeros((len(index), 5)), index)


def test_engine_never_shows_future_to_models():
    idx = pd.date_range("2025-01-01", periods=24 * 200, freq="h", tz="UTC")
    rng = np.random.default_rng(0)
    feats = build_features(
        pd.DataFrame({"log_rv": rng.normal(size=len(idx))}, index=idx))
    origins = make_origins(feats.index, test_days=20, stride_days=5)
    _Spy.seen.clear()
    res = run_backtest(feats, ["_spy"], origins)
    for origin, last_seen in zip(origins, _Spy.seen):
        assert last_seen <= origin
    assert (res["target_time"] > res["origin"]).all()
