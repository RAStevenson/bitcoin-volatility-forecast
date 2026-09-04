"""Rebuild data/hourly_rv.parquet, the hourly realized volatility series,
from the whole minute store, then print the hour count, the NaN hours and
a summary of the rv column. It overwrites the existing parquet rather
than appending to it."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fbench.harness_config import DATA_DIR
from fbench.data import minute_store
from fbench.realized_volatility import hourly_realized_vol

m = minute_store.load_minutes()
s = m.set_index("time")["close"]
out = hourly_realized_vol(s)
out.to_parquet(DATA_DIR / "hourly_rv.parquet")
print("hours:", len(out))
print("nan hours:", int(out["rv"].isna().sum()))
print(out["rv"].describe())
