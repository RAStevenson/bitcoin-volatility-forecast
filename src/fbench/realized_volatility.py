"""Realized volatility from 1-minute closes, defined for a clock hour as
the square root of the summed squared 1-minute log returns inside that
hour, scaled by ANNUALIZER = sqrt(365 * 24) into annualized volatility
units. The hourly frame is indexed in UTC and carries log_rv, the natural
log of that annualized rv, which is the target the models forecast, and
close, the last 1-minute close inside the hour, which the daily forecast scoring
uses to measure the day's price move."""

import numpy as np
import pandas as pd

from fbench.harness_config import ANNUALIZER, MIN_MINUTES_PER_HOUR


def hourly_realized_vol(minute_close):
    """Hourly realized vol from 1-min closes.

    rv = sqrt(sum of squared 1-min log returns in the hour), annualized.
    Hours with fewer than MIN_MINUTES_PER_HOUR returns are NaN rather than
    silently quiet: a data gap must not masquerade as low volatility. The
    close column keeps the hour's last minute close whenever any minute
    exists, since a price is a price however sparse the hour.
    """
    minute_return = np.log(minute_close).diff().dropna()
    return_hour = minute_return.index.floor("h")
    sum_of_squares = minute_return.pow(2).groupby(return_hour).sum()
    n_minutes = minute_return.groupby(return_hour).count()
    hourly = pd.DataFrame({"rv": np.sqrt(sum_of_squares) * ANNUALIZER,
                           "n_minutes": n_minutes})
    hourly.loc[hourly["n_minutes"] < MIN_MINUTES_PER_HOUR, "rv"] = np.nan
    hourly["log_rv"] = np.log(hourly["rv"])
    hourly["close"] = minute_close.groupby(minute_close.index.floor("h")).last()
    every_hour = pd.date_range(hourly.index.min(), hourly.index.max(), freq="h", tz="UTC")
    return hourly.reindex(every_hour)  # absent hours become explicit NaN rows
