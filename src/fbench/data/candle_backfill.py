"""Chunked catch-up of the local minute store from Coinbase, resuming from
the last bar already saved."""

import pandas as pd

from fbench.data import coinbase_client, minute_store
from fbench.harness_config import HISTORY_START, MINUTE_SECONDS, PRODUCT

# Fetch and persist in monthly chunks so an interrupted run loses at most
# one chunk; the watermark then resumes from what was saved.
CHUNK_SPAN = pd.Timedelta(days=30)


def backfill(verbose=True):
    """Bring the minute store up to now. Returns rows added."""
    end = pd.Timestamp.now(tz="UTC").floor("min")
    rows_added = 0
    while True:
        existing = minute_store.load_minutes()
        if existing.empty:
            start = pd.Timestamp(HISTORY_START, tz="UTC")
        else:
            start = existing["time"].max() + pd.Timedelta(
                seconds=MINUTE_SECONDS)
        if start >= end:
            break
        chunk_end = min(start + CHUNK_SPAN, end)
        if verbose:
            print(f"backfilling {PRODUCT}: {start} -> {chunk_end}",
                  flush=True)
        fetched_minutes = coinbase_client.fetch_candles(PRODUCT, start, chunk_end,
                                                        MINUTE_SECONDS)
        merged = (pd.concat([existing, fetched_minutes]).drop_duplicates("time")
                    .sort_values("time").reset_index(drop=True))
        minute_store.save_minutes(merged)
        rows_added += len(fetched_minutes)
        if verbose:
            print(f"  +{len(fetched_minutes)} rows, total {len(merged)}", flush=True)
    return rows_added
