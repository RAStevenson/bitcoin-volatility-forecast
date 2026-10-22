"""Feature builder for the volatility models, turning hourly log realized
volatility into lagged, HAR-style, and time-of-day predictors. The
time-of-day and day-of-week terms are read off the frame's index, which
the pipeline supplies in UTC."""

import numpy as np
import pandas as pd

FEATURE_COLS = ["lag_0", "lag_1", "lag_2", "lag_24", "lag_48", "lag_168",
                "har_d", "har_w", "har_m",
                "hod_sin", "hod_cos", "dow_sin", "dow_cos"]

# A row's predictors use data through the row's own hour and nothing
# after it: lag_0 is the row's own log RV, lag_k the value k hours
# earlier, and the HAR means are trailing windows that end at the row.
# A model fits from rows at or before its origin and forecasts hours
# strictly after it, so the origin hour is the newest closed hour it may
# use and never one of its targets. This is the leakage rule; tests pin
# it.


def build_features(hourly):
    """Return a frame on the same index as hourly, carrying the target
    column log_rv alongside every predictor named in FEATURE_COLS. A
    row's predictors end at the row's own hour, so a row uses no data
    past its own timestamp, and the leading rows stay NaN until the
    windows fill."""
    log_realized_vol = hourly["log_rv"]
    features = pd.DataFrame(index=hourly.index)
    features["log_rv"] = log_realized_vol
    for lag in (0, 1, 2, 24, 48, 168):
        features[f"lag_{lag}"] = log_realized_vol.shift(lag)
    features["har_d"] = log_realized_vol.rolling(24, min_periods=18).mean()
    features["har_w"] = log_realized_vol.rolling(168, min_periods=120).mean()
    features["har_m"] = log_realized_vol.rolling(720, min_periods=500).mean()
    timestamps = pd.DatetimeIndex(features.index)
    hour_of_day = timestamps.hour
    day_of_week = timestamps.dayofweek
    features["hod_sin"] = np.sin(2 * np.pi * hour_of_day / 24)
    features["hod_cos"] = np.cos(2 * np.pi * hour_of_day / 24)
    features["dow_sin"] = np.sin(2 * np.pi * day_of_week / 7)
    features["dow_cos"] = np.cos(2 * np.pi * day_of_week / 7)
    return features
