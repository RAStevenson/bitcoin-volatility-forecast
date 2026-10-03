"""Feature builder for the volatility models, turning hourly log realized
volatility into lagged, HAR-style, and time-of-day predictors. The
time-of-day and day-of-week terms are read off the frame's index, which
the pipeline supplies in UTC."""

import numpy as np
import pandas as pd

FEATURE_COLS = ["lag_1", "lag_2", "lag_3", "lag_24", "lag_48", "lag_168",
                "har_d", "har_w", "har_m",
                "hod_sin", "hod_cos", "dow_sin", "dow_cos"]

# Trailing HAR-style means over the past day/week/month of hourly log RV.
# Everything is shift(1) BEFORE rolling: features at time t use data
# strictly before t. This is the leakage rule; tests pin it.


def build_features(hourly):
    """Return a frame on the same index as hourly, carrying the target
    column log_rv alongside every predictor named in FEATURE_COLS. Each
    predictor is shifted before it is rolled, so a row uses only data
    strictly before its own timestamp, and the leading rows stay NaN
    until the windows fill."""
    lr = hourly["log_rv"]
    f = pd.DataFrame(index=hourly.index)
    f["log_rv"] = lr
    for lag in (1, 2, 3, 24, 48, 168):
        f[f"lag_{lag}"] = lr.shift(lag)
    past = lr.shift(1)
    f["har_d"] = past.rolling(24, min_periods=18).mean()
    f["har_w"] = past.rolling(168, min_periods=120).mean()
    f["har_m"] = past.rolling(720, min_periods=500).mean()
    idx = pd.DatetimeIndex(f.index)
    hod = idx.hour
    dow = idx.dayofweek
    f["hod_sin"] = np.sin(2 * np.pi * hod / 24)
    f["hod_cos"] = np.cos(2 * np.pi * hod / 24)
    f["dow_sin"] = np.sin(2 * np.pi * dow / 7)
    f["dow_cos"] = np.cos(2 * np.pi * dow / 7)
    return f
