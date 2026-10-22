"""Chunked catch-up of the local minute store from Coinbase, resuming from
the last bar already saved."""

import pandas as pd

from fbench.data import coinbase_client, minute_store
from fbench.harness_config import HISTORY_START, MINUTE_SECONDS, PRODUCT

# Fetch and persist in monthly chunks so an interrupted run loses at most
# one chunk; the watermark then resumes from what was saved.
CHUNK_SPAN = pd.Timedelta(days=30)


def backfill(verbose=True, now=None, fetch=None):
    """Bring the minute store up to now, one CHUNK_SPAN at a time from
    the minute after the last saved bar. Returns rows added. The request
    window advances by the chunk whether or not Coinbase returned bars
    for it, so a span its history holds nothing for is skipped rather
    than requested again forever. `now` and `fetch` exist so a test can
    place the clock and supply candles without the network."""
    now = pd.Timestamp.now(tz="UTC") if now is None else now
    fetch = coinbase_client.fetch_candles if fetch is None else fetch
    end = now.floor("min")
    existing = minute_store.load_minutes()
    if existing.empty:
        start = pd.Timestamp(HISTORY_START, tz="UTC")
    else:
        start = existing["time"].max() + pd.Timedelta(seconds=MINUTE_SECONDS)
    rows_added = 0
    while start < end:
        chunk_end = min(start + CHUNK_SPAN, end)
        if verbose:
            print(f"backfilling {PRODUCT}: {start} -> {chunk_end}",
                  flush=True)
        fetched_minutes = fetch(PRODUCT, start, chunk_end, MINUTE_SECONDS)
        if not fetched_minutes.empty:
            existing = (pd.concat([existing, fetched_minutes]).drop_duplicates("time")
                        .sort_values("time").reset_index(drop=True))
            minute_store.save_minutes(existing)
            rows_added += len(fetched_minutes)
        if verbose:
            print(f"  +{len(fetched_minutes)} rows, total {len(existing)}", flush=True)
        start = chunk_end
    return rows_added
