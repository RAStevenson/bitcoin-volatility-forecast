"""Coinbase Exchange public candle client, the primary price source behind
the minute store and the BTC-USD hourly series."""

import time

import pandas as pd
import requests

BASE = "https://api.exchange.coinbase.com"
MAX_CANDLES = 300  # API cap per request


def _get(url, params, attempts=4):
    """Send one GET to the Coinbase public API and return the decoded JSON
    body, backing off exponentially on an HTTP 429 or a transport error.
    Raises after the last attempt, so a run of rate-limit replies fails
    here with its cause rather than later in a caller."""
    for i in range(attempts):
        try:
            r = requests.get(url, params=params, timeout=30)
            if r.status_code == 429:
                time.sleep(2 ** i)
                continue
            r.raise_for_status()
            return r.json()
        except requests.RequestException:
            if i == attempts - 1:
                raise
            time.sleep(2 ** i)
    raise requests.HTTPError(f"{url}: rate limited on all {attempts} attempts")


def fetch_candles(product, start, end, granularity):
    """Candles in [start, end), paginated at the 300-candle API cap."""
    out = []
    step = pd.Timedelta(seconds=granularity * MAX_CANDLES)
    cur = start
    while cur < end:
        chunk_end = min(cur + step, end)
        rows = _get(f"{BASE}/products/{product}/candles",
                    {"granularity": granularity,
                     "start": cur.isoformat(), "end": chunk_end.isoformat()})
        out.extend(rows)
        cur = chunk_end
        time.sleep(0.15)  # stay far inside the public rate limit
    df = pd.DataFrame(out, columns=["ts", "low", "high", "open", "close",
                                    "volume"])
    if df.empty:
        return df
    df["time"] = pd.to_datetime(df["ts"], unit="s", utc=True)
    return (df.drop(columns="ts").drop_duplicates("time")
              .sort_values("time").reset_index(drop=True))
