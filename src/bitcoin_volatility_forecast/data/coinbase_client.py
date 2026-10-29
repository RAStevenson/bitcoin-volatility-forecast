"""Coinbase Exchange public candle client, the price source behind the
minute store and the BTC-USD hourly series."""

import time

import pandas as pd
import requests

BASE_URL = "https://api.exchange.coinbase.com"
MAX_CANDLES = 300  # API cap per request


def _get(url, params, attempts=4):
    """Send one GET to the Coinbase public API and return the decoded JSON
    body, backing off exponentially on an HTTP 429 or a transport error.
    Raises after the last attempt, so a run of rate-limit replies fails
    here with its cause rather than later in a caller."""
    for attempt in range(attempts):
        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            if attempt == attempts - 1:
                raise
            time.sleep(2 ** attempt)
    raise requests.HTTPError(f"{url}: rate limited on all {attempts} attempts")


def fetch_candles(product, start, end, granularity):
    """Candles in [start, end), paginated at the 300-candle API cap."""
    candle_rows = []
    chunk_span = pd.Timedelta(seconds=granularity * MAX_CANDLES)
    chunk_start = start
    while chunk_start < end:
        chunk_end = min(chunk_start + chunk_span, end)
        rows = _get(f"{BASE_URL}/products/{product}/candles",
                    {"granularity": granularity,
                     "start": chunk_start.isoformat(), "end": chunk_end.isoformat()})
        candle_rows.extend(rows)
        chunk_start = chunk_end
        time.sleep(0.15)  # stay far inside the public rate limit
    candles = pd.DataFrame(candle_rows, columns=["ts", "low", "high", "open", "close",
                                                 "volume"])
    candles["time"] = pd.to_datetime(candles["ts"], unit="s", utc=True)
    # An empty result keeps the same columns as a full one, time included,
    # so a caller that concatenates or reads "time" needs no special case.
    return (candles.drop(columns="ts").drop_duplicates("time")
            .sort_values("time").reset_index(drop=True)
            [["time", "low", "high", "open", "close", "volume"]])
