"""The committed hourly realized-volatility series, data/hourly_rv.csv,
and the daily update that extends it. The daily run fetches only the
minutes since the last stored hour, builds the complete hours among
them, and appends those, so the repo carries the hourly series and no
minute history. A full rebuild from a local minute store is
scripts/run_build_rv.py."""

import pandas as pd

from fbench.data import coinbase_client
from fbench.harness_config import HOURLY_PATH, MINUTE_SECONDS, PRODUCT
from fbench.realized_volatility import hourly_realized_vol

COLUMNS = ["rv", "n_minutes", "log_rv", "close"]


def load_hourly():
    """Read data/hourly_rv.csv into a frame indexed by UTC hour, with the
    columns realized_volatility.hourly_realized_vol produces, or raise
    FileNotFoundError naming run_build_rv.py when the file is absent."""
    if not HOURLY_PATH.exists():
        raise FileNotFoundError(
            f"{HOURLY_PATH} is missing; build it with scripts/run_build_rv.py "
            "from a local minute store")
    # round_trip parsing: the default C parser can land a float one unit
    # in the last place away from what was written, and a rewritten row
    # would then differ from the committed one.
    hourly = pd.read_csv(HOURLY_PATH, index_col="time", parse_dates=["time"],
                         float_precision="round_trip")
    hour_index = pd.DatetimeIndex(hourly.index)
    hourly.index = (hour_index.tz_localize("UTC") if hour_index.tz is None
                    else hour_index.tz_convert("UTC"))
    return hourly[COLUMNS]


def save_hourly(hourly):
    """Write the hourly frame to data/hourly_rv.csv with the index labeled time,
    creating data/ if needed, and return the path. Rows already on disk
    are rewritten with identical text, since pandas writes floats by
    their shortest exact representation, so git sees only the appended
    lines change."""
    HOURLY_PATH.parent.mkdir(exist_ok=True)
    hourly[COLUMNS].rename_axis("time").to_csv(HOURLY_PATH, lineterminator="\n")
    return HOURLY_PATH


def complete_hours(hourly, now):
    """The rows of hourly whose hour had ended by now, so a partial hour in
    progress is never stored as if it were finished."""
    return hourly[hourly.index + pd.Timedelta(hours=1) <= now]


def update_hourly(now=None, fetch=None):
    """Extend the stored series to the last complete hour before now.
    Fetches minutes from one minute before the last stored hour (the
    return into that hour's first minute needs the prior close), rebuilds
    that hour and every complete hour after it, replaces the last stored
    hour with the rebuilt one, and saves. Returns the updated frame, the
    latest minute close fetched (the price the daily forecast quotes),
    and the number of minutes fetched. `now` and `fetch` exist so a test
    can place the clock and supply minutes without the network."""
    now = pd.Timestamp.now(tz="UTC") if now is None else now
    fetch = coinbase_client.fetch_candles if fetch is None else fetch
    stored = load_hourly()
    cut = stored.index[-1]
    minutes = fetch(PRODUCT, cut - pd.Timedelta(minutes=1), now.floor("min"),
                    MINUTE_SECONDS)
    if minutes.empty:
        return stored, float(stored["close"].dropna().iloc[-1]), 0
    fresh = hourly_realized_vol(minutes.set_index("time")["close"])
    fresh = complete_hours(fresh[fresh.index >= cut], now)
    merged = pd.concat([stored[stored.index < cut], fresh])
    grid = pd.date_range(merged.index.min(), merged.index.max(), freq="h",
                         tz="UTC")
    merged = merged.reindex(grid)
    save_hourly(merged)
    return merged, float(minutes["close"].iloc[-1]), len(minutes)
