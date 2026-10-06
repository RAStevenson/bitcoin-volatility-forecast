"""Walk-forward backtest driver, running each registered model from a
series of rolling origins and collecting its quantile forecasts next to
the realized outcomes."""

import pandas as pd

from fbench.harness_config import HORIZON
from fbench.models.base_forecast_model import REGISTRY


def make_origins(timestamps, test_days, stride_days):
    """Forecast origins for the backtest, one every stride_days across
    the test_days window that stops a day short of the last midnight in
    timestamps, returned as UTC midnight timestamps. An origin is the latest
    timestamp a model may see when it fits, so every hour it forecasts
    falls strictly after it."""
    last_midnight = timestamps[-1].floor("D")
    first_origin = last_midnight - pd.Timedelta(days=test_days)
    return pd.date_range(first_origin, last_midnight - pd.Timedelta(days=1),
                         freq=f"{stride_days}D", tz="UTC")


def run_backtest(features, model_names, origins, horizon=HORIZON):
    """Fit each named model at each origin and predict the next horizon
    hours, returning one long frame in which a row is a single (origin,
    model, target hour) carrying the five quantile columns, the horizon
    step from 1 to horizon, and y_true for that hour. The quantiles and
    y_true are in log realized-volatility space, and y_true is NaN for
    any target hour features holds no outcome for."""
    forecast_frames = []
    for origin in origins:
        future = pd.date_range(origin + pd.Timedelta(hours=1),
                               periods=horizon, freq="h", tz="UTC")
        for model_name in model_names:
            model_class = REGISTRY[model_name]
            training_rows = features.loc[
                origin - pd.Timedelta(days=model_class.train_days):origin]
            # The two guards below ARE the leakage policy. Never remove.
            assert training_rows.index.max() <= origin
            assert future.min() > origin
            model = model_class()
            model.fit(training_rows)
            quantile_forecast = model.predict(future)
            quantile_forecast = quantile_forecast.assign(
                origin=origin, model=model_name,
                horizon=range(1, horizon + 1),
                y_true=features["log_rv"].reindex(future).to_numpy())
            forecast_frames.append(
                quantile_forecast.rename_axis("target_time").reset_index())
    return pd.concat(forecast_frames, ignore_index=True)
