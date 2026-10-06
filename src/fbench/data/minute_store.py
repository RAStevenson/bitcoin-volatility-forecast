"""Parquet store holding the minute bar history on disk, and the grid gap
check that audits it."""

import pandas as pd

from fbench.harness_config import DATA_DIR, PRODUCT


def minute_path():
    """Return the parquet path holding minute bars for the product named in
    the config, under the repo's data directory. The product id is part of
    the file name, so changing PRODUCT points at a different file rather
    than migrating the one already written.
    """
    return DATA_DIR / f"minute_{PRODUCT}.parquet"


def load_minutes():
    """Read the whole minute parquet for the configured product into memory,
    giving a frame with UTC `time` beside the OHLC and volume columns. A
    store that has never been written comes back as a frame with no rows and
    no columns at all, so check `.empty` before reaching for `time`.
    """
    path = minute_path()
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)


def save_minutes(minutes):
    """Write the minute frame to the configured product's minute parquet without its
    index, creating the data directory if it is missing. The file is replaced
    whole, so a caller adding rows merges them into the loaded frame first
    instead of expecting an append.
    """
    DATA_DIR.mkdir(exist_ok=True)
    minutes.to_parquet(minute_path(), index=False)


def gap_report(bars, granularity_seconds):
    """Count and locate missing bars against a complete regular grid."""
    expected_times = pd.date_range(bars["time"].min(), bars["time"].max(),
                                   freq=f"{granularity_seconds}s", tz="UTC")
    missing_times = expected_times.difference(pd.DatetimeIndex(bars["time"]))
    return {"expected": len(expected_times), "present": len(bars),
            "missing": len(missing_times),
            "missing_sample": list(missing_times[:10].astype(str))}
