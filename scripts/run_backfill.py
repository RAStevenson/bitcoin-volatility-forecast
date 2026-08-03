import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

import pandas as pd

from fbench.config import HISTORY_START, MINUTE_SECONDS, PRODUCT
from fbench.data import coinbase, store

# Fetch and persist in monthly chunks so an interrupted run loses at most
# one chunk; the watermark then resumes from what was saved.
CHUNK = pd.Timedelta(days=30)

end = pd.Timestamp.now(tz="UTC").floor("min")
while True:
    existing = store.load_minutes()
    if existing.empty:
        start = pd.Timestamp(HISTORY_START, tz="UTC")
    else:
        start = existing["time"].max() + pd.Timedelta(seconds=MINUTE_SECONDS)
    if start >= end:
        break
    chunk_end = min(start + CHUNK, end)
    print(f"backfilling {PRODUCT}: {start} -> {chunk_end}", flush=True)
    new = coinbase.fetch_candles(PRODUCT, start, chunk_end, MINUTE_SECONDS)
    merged = (pd.concat([existing, new]).drop_duplicates("time")
                .sort_values("time").reset_index(drop=True))
    store.save_minutes(merged)
    print(f"  +{len(new)} rows, total {len(merged)}", flush=True)

final = store.load_minutes()
print("total rows:", len(final))
print(store.gap_report(final, MINUTE_SECONDS))
