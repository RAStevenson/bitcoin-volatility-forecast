import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

import argparse
import json
import time

import pandas as pd

import fbench.models.gbm  # noqa: F401  (register the classical field)
import fbench.models.har  # noqa: F401
import fbench.models.persistence  # noqa: F401
import fbench.models.prophet_model  # noqa: F401
import fbench.models.sarima  # noqa: F401
from fbench.backtest import make_origins, run_backtest
from fbench.config import RESULTS_DIR
from fbench.data.load_demo import LOAD_PATH, fetch_load
from fbench.features import build_features
from fbench.models.base import REGISTRY
from fbench.report import write_report
from fbench.scoring import add_skill, score

parser = argparse.ArgumentParser()
parser.add_argument("--stride", type=int, default=4)
parser.add_argument("--test-days", type=int, default=365)
args = parser.parse_args()

if LOAD_PATH.exists():
    hourly = pd.read_parquet(LOAD_PATH)
else:
    print("fetching OPSD load data (~250 MB, one time)", flush=True)
    hourly = fetch_load()
print(f"load series: {len(hourly)} hours, "
      f"{hourly.index.min()} -> {hourly.index.max()}, "
      f"NaN hours: {int(hourly['rv'].isna().sum())}", flush=True)

feats = build_features(hourly)
origins = make_origins(feats.index, args.test_days, args.stride)
names = [n for n in sorted(REGISTRY) if not n.startswith("_")]
print(f"models={names} origins={len(origins)}", flush=True)

rows = []
for name in names:
    t0 = time.perf_counter()
    rows.append(run_backtest(feats, [name], origins))
    print(f"{name}: {time.perf_counter() - t0:.1f}s", flush=True)
res = pd.concat(rows, ignore_index=True)

RESULTS_DIR.mkdir(exist_ok=True)
# Named load_* so run_report's backtest_* glob never picks it up.
out = RESULTS_DIR / "load_backtest_DE.parquet"
res.to_parquet(out, index=False)
out.with_suffix(".json").write_text(json.dumps(
    {"stride": args.stride, "test_days": args.test_days,
     "series": "DE_load_actual_entsoe_transparency",
     "origins": len(origins)}))

scores = add_skill(score(res))
path = write_report(
    scores, hourly, out, out_name="LOAD_REPORT.md", fig_prefix="fig_load",
    title="Generality demo: German hourly load (OPSD/ENTSO-E, CC-BY 4.0)",
    value_label="median load (MW)")
print(f"report -> {path}")
print(scores.groupby("model")["pinball_mean"].mean().sort_values())
