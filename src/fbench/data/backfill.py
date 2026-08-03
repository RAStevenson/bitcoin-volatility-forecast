import pandas as pd

from fbench.config import HISTORY_START, MINUTE_SECONDS, PRODUCT
from fbench.data import coinbase, store

# Fetch and persist in monthly chunks so an interrupted run loses at most
# one chunk; the watermark then resumes from what was saved.
CHUNK = pd.Timedelta(days=30)


def backfill(verbose=True):
    """Bring the minute store up to now. Returns rows added."""
    end = pd.Timestamp.now(tz="UTC").floor("min")
    added = 0
    while True:
        existing = store.load_minutes()
        if existing.empty:
            start = pd.Timestamp(HISTORY_START, tz="UTC")
        else:
            start = existing["time"].max() + pd.Timedelta(
                seconds=MINUTE_SECONDS)
        if start >= end:
            break
        chunk_end = min(start + CHUNK, end)
        if verbose:
            print(f"backfilling {PRODUCT}: {start} -> {chunk_end}",
                  flush=True)
        new = coinbase.fetch_candles(PRODUCT, start, chunk_end,
                                     MINUTE_SECONDS)
        merged = (pd.concat([existing, new]).drop_duplicates("time")
                    .sort_values("time").reset_index(drop=True))
        store.save_minutes(merged)
        added += len(new)
        if verbose:
            print(f"  +{len(new)} rows, total {len(merged)}", flush=True)
    return added
