"""Check the local Coinbase minute data against a second venue by pulling
Bitstamp hourly candles over the same span and reporting how far the two
sets of hourly closes diverge. It calls the Bitstamp API and writes
results/crosscheck.txt as well as printing the figures."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd

from fbench.data import bitstamp_client, minute_store
from fbench.harness_config import BITSTAMP_PAIR, RESULTS_DIR

minutes = minute_store.load_minutes()
coinbase_close = (minutes.set_index("time")["close"].groupby(pd.Grouper(freq="h")).last()
                  .rename("coinbase_close").dropna())
print(f"fetching Bitstamp hourly {coinbase_close.index.min()} -> "
      f"{coinbase_close.index.max()}", flush=True)
bitstamp_hourly = bitstamp_client.fetch_hourly(BITSTAMP_PAIR, coinbase_close.index.min(),
                                               coinbase_close.index.max())
bitstamp_with_coinbase = bitstamp_hourly.set_index("time").join(coinbase_close,
                                                                how="inner")
relative_difference = ((bitstamp_with_coinbase["coinbase_close"]
                        - bitstamp_with_coinbase["close"]).abs()
                       / bitstamp_with_coinbase["close"])
lines = [
    f"hours compared: {len(bitstamp_with_coinbase)}",
    f"median abs pct diff: {relative_difference.median():.5%}",
    f"p99 abs pct diff: {relative_difference.quantile(0.99):.5%}",
    f"hours over 0.5% divergence: {(relative_difference > 0.005).sum()}",
]
RESULTS_DIR.mkdir(exist_ok=True)
(RESULTS_DIR / "crosscheck.txt").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
