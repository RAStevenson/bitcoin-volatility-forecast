"""Walk-forward backtest driver, running each registered model from a
series of rolling origins and collecting its quantile forecasts next to
the realized outcomes."""

import pandas as pd

from bitcoin_volatility_forecast.forecast_settings import HORIZON
from bitcoin_volatility_forecast.models.base_forecast_model import REGISTRY


def check_no_future(training_rows, target_times, origin):
    """Raise ValueError if any training row falls after origin or any
    target hour falls at or before it. This is the leakage policy that
    the backtest and the daily run both enforce before every fit. It
    raises rather than asserts, so it holds even when Python runs with
    assertions switched off."""
    if training_rows.index.max() > origin:
        raise ValueError(f"training data runs to {training_rows.index.max()}, "
                         f"past the origin {origin}")
    if pd.DatetimeIndex(target_times).min() <= origin:
        raise ValueError(f"a target hour, {pd.DatetimeIndex(target_times).min()}, "
                         f"is not after the origin {origin}")


def make_origins(timestamps, test_days, stride_days, origin_hour_utc=0):
    """Forecast origins for the backtest, one every stride_days across a
    test_days window, each at origin_hour_utc on its day. An origin is
    the latest timestamp a model may see when it fits, so every hour it
    forecasts falls strictly after it. The last origin is the latest one
    whose 24 target hours all sit inside timestamps, and the first is
    test_days - 1 days before it, so a given test_days and stride give
    the same count of origins at any hour."""
    last_hour = timestamps[-1]
    last_origin = (last_hour - pd.Timedelta(hours=HORIZON)).floor("D") + pd.Timedelta(
        hours=origin_hour_utc)
    if last_origin + pd.Timedelta(hours=HORIZON) > last_hour:
        last_origin -= pd.Timedelta(days=1)
    first_origin = last_origin - pd.Timedelta(days=test_days - 1)
    return pd.date_range(first_origin, last_origin, freq=f"{stride_days}D", tz="UTC")


def run_backtest(features, model_names, origins, horizon=HORIZON, registry=None):
    """Fit each named model at each origin and predict the next horizon
    hours, returning one long frame in which a row is a single (origin,
    model, target hour) carrying the five quantile columns, the horizon
    step from 1 to horizon, and y_true for that hour. The quantiles and
    y_true are in log realized-volatility space, and y_true is NaN for
    any target hour features holds no outcome for. Models are looked up
    in registry, the package REGISTRY unless a caller such as the tuning
    script passes its own mapping of names to model classes."""
    registry = REGISTRY if registry is None else registry
    forecast_frames = []
    for origin in origins:
        future = pd.date_range(origin + pd.Timedelta(hours=1),
                               periods=horizon, freq="h", tz="UTC")
        for model_name in model_names:
            model_class = registry[model_name]
            training_rows = features.loc[
                origin - pd.Timedelta(days=model_class.train_days):origin]
            # The leakage policy. Never remove.
            check_no_future(training_rows, future, origin)
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
