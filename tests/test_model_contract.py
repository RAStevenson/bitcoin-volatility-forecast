import warnings

import numpy as np
import pandas as pd
import pytest

import bitcoin_volatility_forecast.models.har_model
import bitcoin_volatility_forecast.models.nhits_model
import bitcoin_volatility_forecast.models.persistence_model
import bitcoin_volatility_forecast.models.prophet_model
import bitcoin_volatility_forecast.models.sarima_model
import bitcoin_volatility_forecast.models.xgboost_model  # noqa: F401  (registers)
from bitcoin_volatility_forecast.feature_builder import build_features
from bitcoin_volatility_forecast.forecast_settings import HORIZON, QCOLS
from bitcoin_volatility_forecast.models.base_forecast_model import REGISTRY
from bitcoin_volatility_forecast.models.nhits_model import _block_listed_warnings


def test_nhits_blocks_only_its_listed_warnings():
    with warnings.catch_warnings(record=True) as recorded_warnings:
        warnings.simplefilter("always")
        with warnings.catch_warnings():
            _block_listed_warnings()
            warnings.warn("The 'train_dataloader' does not have many workers "
                          "which may be a bottleneck.", UserWarning, stacklevel=1)
            warnings.warn("the loss is NaN", UserWarning, stacklevel=1)
    assert [str(warning.message) for warning in recorded_warnings] == ["the loss is NaN"]


def _train(n_hours=24 * 400, seed=1):
    timestamps = pd.date_range("2025-01-01", periods=n_hours, freq="h", tz="UTC")
    random_generator = np.random.default_rng(seed)
    log_realized_vol = pd.Series(random_generator.normal(0, 0.3, n_hours),
                                 index=timestamps).rolling(3).mean()
    return build_features(pd.DataFrame({"log_rv": log_realized_vol}))


@pytest.mark.parametrize("model_name", sorted(REGISTRY))
def test_contract(model_name):
    training_rows = _train()
    future = pd.date_range(training_rows.index[-1] + pd.Timedelta(hours=1),
                           periods=HORIZON, freq="h", tz="UTC")
    model = REGISTRY[model_name]()
    model.fit(training_rows)
    quantile_forecast = model.predict(future)
    assert list(quantile_forecast.columns) == QCOLS
    assert quantile_forecast.index.equals(future)
    assert quantile_forecast.notna().all().all()
    quantile_values = quantile_forecast.to_numpy()
    assert (quantile_values[:, :-1] <= quantile_values[:, 1:]).all()  # monotone
