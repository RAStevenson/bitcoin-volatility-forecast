import warnings

import numpy as np
import pandas as pd
import pytest

import fbench.models.har_model
import fbench.models.nhits_model
import fbench.models.persistence_model
import fbench.models.prophet_model
import fbench.models.sarima_model
import fbench.models.xgboost_model  # noqa: F401  (registers)
from fbench.feature_builder import build_features
from fbench.harness_config import HORIZON, QCOLS
from fbench.models.base_forecast_model import REGISTRY
from fbench.models.nhits_model import _block_listed_warnings


def test_nhits_blocks_only_its_listed_warnings():
    with warnings.catch_warnings(record=True) as seen:
        warnings.simplefilter("always")
        with warnings.catch_warnings():
            _block_listed_warnings()
            warnings.warn("The 'train_dataloader' does not have many workers "
                          "which may be a bottleneck.", UserWarning, stacklevel=1)
            warnings.warn("the loss is NaN", UserWarning, stacklevel=1)
    assert [str(warning.message) for warning in seen] == ["the loss is NaN"]


def _train(n_hours=24 * 400, seed=1):
    timestamps = pd.date_range("2025-01-01", periods=n_hours, freq="h", tz="UTC")
    rng = np.random.default_rng(seed)
    log_realized_vol = pd.Series(rng.normal(0, 0.3, n_hours),
                                 index=timestamps).rolling(3).mean()
    return build_features(pd.DataFrame({"log_rv": log_realized_vol}))


@pytest.mark.parametrize("model_name", sorted(REGISTRY))
def test_contract(model_name):
    train = _train()
    future = pd.date_range(train.index[-1] + pd.Timedelta(hours=1),
                           periods=HORIZON, freq="h", tz="UTC")
    model = REGISTRY[model_name]()
    model.fit(train)
    out = model.predict(future)
    assert list(out.columns) == QCOLS
    assert out.index.equals(future)
    assert out.notna().all().all()
    assert (out.values[:, :-1] <= out.values[:, 1:]).all()  # monotone
