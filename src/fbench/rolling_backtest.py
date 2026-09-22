"""Walk-forward backtest driver, running each registered model from a
series of rolling origins and collecting its quantile forecasts next to
the realized outcomes."""

import pandas as pd

from fbench.harness_config import HORIZON
from src.fbench.models.base_forecast_model import REGISTRY


def make_origins(index, test_days, stride_days):
    """Forecast origins for the backtest, one every stride_days across
    the test_days window that stops a day short of the last midnight in
    index, returned as UTC midnight timestamps. An origin is the latest
    timestamp a model may see when it fits, so every hour it forecasts
    falls strictly after it."""
    last_full = index[-1].floor("D")
    start = last_full - pd.Timedelta(days=test_days)
    return pd.date_range(start, last_full - pd.Timedelta(days=1),
                         freq=f"{stride_days}D", tz="UTC")


def run_backtest(feats, model_names, origins, horizon=HORIZON):
    """Fit each named model at each origin and predict the next horizon
    hours, returning one long frame in which a row is a single (origin,
    model, target hour) carrying the five quantile columns, the horizon
    step from 1 to horizon, and y_true for that hour. The quantiles and
    y_true are in log realized-volatility space, and y_true is NaN for
    any target hour feats holds no outcome for."""
    out = []
    for origin in origins:
        future = pd.date_range(origin + pd.Timedelta(hours=1),
                               periods=horizon, freq="h", tz="UTC")
        for name in model_names:
            cls = REGISTRY[name]
            train = feats.loc[origin - pd.Timedelta(days=cls.train_days):
                              origin]
            # The two guards below ARE the leakage policy. Never remove.
            assert train.index.max() <= origin
            assert future.min() > origin
            m = cls()
            m.fit(train)
            q = m.predict(future)
            q = q.assign(origin=origin, model=name,
                         horizon=range(1, horizon + 1),
                         y_true=feats["log_rv"].reindex(future).to_numpy())
            out.append(q.rename_axis("target_time").reset_index())
    return pd.concat(out, ignore_index=True)
