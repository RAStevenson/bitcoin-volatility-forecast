"""Bitstamp hourly OHLC client, the independent second price source the
Coinbase cross-check compares against."""

import time

import pandas as pd
import requests

BASE_URL = "https://www.bitstamp.net/api/v2/ohlc"
MAX_CANDLES = 1000  # API cap per request


def fetch_hourly(pair, start, end):
    """Walk Bitstamp's paged hourly candles for one pair from start up to
    end, returning a frame of UTC `time` and float `close` sorted ascending
    on a fresh index. A pair or window Bitstamp has no data for raises a
    KeyError rather than returning an empty frame, because the column cast
    runs on an empty result.
    """
    candle_rows = []
    page_start_seconds = int(start.timestamp())
    end_seconds = int(end.timestamp())
    while page_start_seconds < end_seconds:
        response = requests.get(f"{BASE_URL}/{pair}/",
                                params={"step": 3600, "limit": MAX_CANDLES,
                                        "start": page_start_seconds},
                                timeout=30)
        response.raise_for_status()
        rows = response.json()["data"]["ohlc"]
        if not rows:
            break
        candle_rows.extend(rows)
        page_start_seconds = int(rows[-1]["timestamp"]) + 3600
        time.sleep(0.2)
    candles = pd.DataFrame(candle_rows)
    candles["time"] = pd.to_datetime(candles["timestamp"].astype(int), unit="s",
                                     utc=True)
    candles["close"] = candles["close"].astype(float)
    return (candles[["time", "close"]].drop_duplicates("time")
            .sort_values("time").reset_index(drop=True))
