import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from fbench.config import DATA_DIR
from fbench.data import store
from fbench.rv import hourly_realized_vol

m = store.load_minutes()
s = m.set_index("time")["close"]
out = hourly_realized_vol(s)
out.to_parquet(DATA_DIR / "hourly_rv.parquet")
print("hours:", len(out))
print("nan hours:", int(out["rv"].isna().sum()))
print(out["rv"].describe())
