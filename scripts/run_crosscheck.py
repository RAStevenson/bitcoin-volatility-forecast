"""Check the local Coinbase minute data against a second venue by pulling
Bitstamp hourly candles over the same span and reporting how far the two
sets of hourly closes diverge. It calls the Bitstamp API and writes
results/crosscheck.txt as well as printing the figures."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd

from fbench.config import BITSTAMP_PAIR, RESULTS_DIR
from fbench.data import bitstamp, store

m = store.load_minutes()
cb = (m.set_index("time")["close"].groupby(pd.Grouper(freq="h")).last()
        .rename("cb_close").dropna())
print(f"fetching Bitstamp hourly {cb.index.min()} -> {cb.index.max()}",
      flush=True)
bs = bitstamp.fetch_hourly(BITSTAMP_PAIR, cb.index.min(), cb.index.max())
j = bs.set_index("time").join(cb, how="inner")
pct = (j["cb_close"] - j["close"]).abs() / j["close"]
lines = [
    f"hours compared: {len(j)}",
    f"median abs pct diff: {pct.median():.5%}",
    f"p99 abs pct diff: {pct.quantile(0.99):.5%}",
    f"hours over 0.5% divergence: {(pct > 0.005).sum()}",
]
RESULTS_DIR.mkdir(exist_ok=True)
(RESULTS_DIR / "crosscheck.txt").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
