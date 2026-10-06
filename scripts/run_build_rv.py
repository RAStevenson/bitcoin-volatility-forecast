"""Rebuild data/hourly_rv.csv, the committed hourly realized volatility
series, from the whole local minute store, keeping only hours that have
ended, then print the hour count, the NaN hours and a summary of the rv
column. It overwrites the existing file rather than appending to it;
the daily run extends the file instead."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import argparse

import pandas as pd

from fbench.data import minute_store
from fbench.data.hourly_series import complete_hours, save_hourly
from fbench.realized_volatility import hourly_realized_vol


def main():
    """Rebuilds data/hourly_rv.csv from the whole minute store and prints
    the hour count, the NaN hours, and a summary of rv."""
    # No options; parsing still runs so --help prints the description
    # and an unknown flag stops the script before it touches any data.
    argparse.ArgumentParser(description=__doc__).parse_args()
    minutes = minute_store.load_minutes()
    minute_close = minutes.set_index("time")["close"]
    hourly = complete_hours(hourly_realized_vol(minute_close), pd.Timestamp.now(tz="UTC"))
    save_hourly(hourly)
    print("hours:", len(hourly))
    print("nan hours:", int(hourly["rv"].isna().sum()))
    print(hourly["rv"].describe())


if __name__ == "__main__":
    main()
