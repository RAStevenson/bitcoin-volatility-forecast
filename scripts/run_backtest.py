import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

import argparse
import json
import time

import pandas as pd

import fbench.models.persistence  # noqa: F401  (registers baselines)
from fbench.backtest import make_origins, run_backtest
from fbench.config import (DATA_DIR, HORIZON, ORIGIN_STRIDE_DAYS,
                           RESULTS_DIR, TEST_DAYS)
from fbench.features import build_features
from fbench.models.base import REGISTRY

# Contender modules are imported as their plan tasks land; each import
# registers its model class as a side effect.
for mod in ("har", "sarima", "prophet_model", "gbm", "nhits"):
    try:
        __import__(f"fbench.models.{mod}")
    except ImportError:
        pass

parser = argparse.ArgumentParser()
parser.add_argument("--models", default=",".join(sorted(REGISTRY)))
parser.add_argument("--stride", type=int, default=ORIGIN_STRIDE_DAYS)
parser.add_argument("--test-days", type=int, default=TEST_DAYS)
args = parser.parse_args()
names = [n for n in args.models.split(",") if not n.startswith("_")]

hourly = pd.read_parquet(DATA_DIR / "hourly_rv.parquet")
feats = build_features(hourly)
origins = make_origins(feats.index, args.test_days, args.stride)
print(f"models={names} origins={len(origins)}", flush=True)

rows, t_all = [], time.perf_counter()
for name in names:
    t0 = time.perf_counter()
    rows.append(run_backtest(feats, [name], origins))
    print(f"{name}: {time.perf_counter() - t0:.1f}s", flush=True)
res = pd.concat(rows, ignore_index=True)

RESULTS_DIR.mkdir(exist_ok=True)
stamp = pd.Timestamp.now(tz="UTC").strftime("%Y%m%d")
out = RESULTS_DIR / f"backtest_{stamp}.parquet"
res.to_parquet(out, index=False)
(out.with_suffix(".json")).write_text(json.dumps(
    {"stride": args.stride, "test_days": args.test_days,
     "horizon": HORIZON, "models": names, "origins": len(origins)}))
print(f"rows={len(res)} -> {out.name}  total {time.perf_counter()-t_all:.0f}s")
