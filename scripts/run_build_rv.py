"""Rebuild data/hourly_rv.csv, the committed hourly realized volatility
series, from the whole local minute store, keeping only hours that have
ended, then print the hour count, the NaN hours and a summary of the rv
column. It overwrites the existing file rather than appending to it;
the daily run extends the file instead."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd

from fbench.data import minute_store
from fbench.data.hourly_series import complete_hours, save_hourly
from fbench.realized_volatility import hourly_realized_vol

m = minute_store.load_minutes()
s = m.set_index("time")["close"]
out = complete_hours(hourly_realized_vol(s), pd.Timestamp.now(tz="UTC"))
save_hourly(out)
print("hours:", len(out))
print("nan hours:", int(out["rv"].isna().sum()))
print(out["rv"].describe())
