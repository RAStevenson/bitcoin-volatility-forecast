import numpy as np
import pandas as pd

from bitcoin_volatility_forecast.forecast_settings import ANNUALIZER
from bitcoin_volatility_forecast.realized_volatility import hourly_realized_vol


def _minutes(n_minutes, start="2026-01-01", minute_return=0.001):
    timestamps = pd.date_range(start, periods=n_minutes, freq="min", tz="UTC")
    prices = 100 * np.exp(np.arange(n_minutes) * minute_return)
    return pd.Series(prices, index=timestamps)


def test_constant_return_hour_matches_closed_form():
    # Assert on hour 1, an interior hour with exactly 60 returns. Hour 0
    # only has 59: diff() consumes the first price, and the return stamped
    # 01:00 (spanning 00:59-01:00) belongs to hour 1 by floor convention.
    closes = _minutes(121)  # covers hours 0 and 1 fully
    hourly = hourly_realized_vol(closes)
    assert hourly["n_minutes"].iloc[1] == 60
    expected = np.sqrt(60 * 0.001 ** 2) * ANNUALIZER
    assert abs(hourly["rv"].iloc[1] - expected) < 1e-9


def test_close_is_the_hours_last_minute():
    closes = _minutes(121)
    hourly = hourly_realized_vol(closes)
    # hour 1 spans minutes 60 to 119; its close is the price at minute 119
    assert hourly["close"].iloc[1] == closes.iloc[119]


def test_sparse_hour_is_nan():
    closes = _minutes(61)
    sparse = closes.drop(closes.index[10:40])  # 30 minutes removed from hour 0
    hourly = hourly_realized_vol(sparse)
    assert np.isnan(hourly["rv"].iloc[0])


def test_missing_hour_appears_as_nan_row():
    first_closes = _minutes(61)
    later_closes = _minutes(61, start="2026-01-01 03:00")
    hourly = hourly_realized_vol(pd.concat([first_closes, later_closes]))
    assert pd.isna(hourly.loc["2026-01-01 01:00+00:00", "rv"])
