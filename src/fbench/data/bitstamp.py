"""Bitstamp hourly OHLC client, the independent second price source the
Coinbase cross-check compares against."""

import time

import pandas as pd
import requests

BASE = "https://www.bitstamp.net/api/v2/ohlc"
LIMIT = 1000


def fetch_hourly(pair, start, end):
    """Walk Bitstamp's paged hourly candles for one pair from start up to
    end, returning a frame of UTC `time` and float `close` sorted ascending
    on a fresh index. A pair or window Bitstamp has no data for raises a
    KeyError rather than returning an empty frame, because the column cast
    runs on an empty result.
    """
    out = []
    cur = int(start.timestamp())
    end_s = int(end.timestamp())
    while cur < end_s:
        r = requests.get(f"{BASE}/{pair}/",
                         params={"step": 3600, "limit": LIMIT, "start": cur},
                         timeout=30)
        r.raise_for_status()
        rows = r.json()["data"]["ohlc"]
        if not rows:
            break
        out.extend(rows)
        cur = int(rows[-1]["timestamp"]) + 3600
        time.sleep(0.2)
    df = pd.DataFrame(out)
    df["time"] = pd.to_datetime(df["timestamp"].astype(int), unit="s",
                                utc=True)
    df["close"] = df["close"].astype(float)
    return (df[["time", "close"]].drop_duplicates("time")
            .sort_values("time").reset_index(drop=True))
