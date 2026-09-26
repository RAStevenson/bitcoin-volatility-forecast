"""Run the model backtest over data/hourly_rv.csv and save the
scored rows as results/backtest_<date>.parquet with a json sidecar
holding the run's settings and a snapshot of the dataset it saw. Unless
--no-report is given it also writes results/REPORT.md with its two
figures and logs the backtest to MLflow."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import argparse
import json
import time

import pandas as pd

import fbench.models.persistence_model  # noqa: F401  (registers baselines)
from fbench.rolling_backtest import make_origins, run_backtest
from fbench.harness_config import (HORIZON, ORIGIN_STRIDE_DAYS, RESULTS_DIR,
                           TEST_DAYS)
from fbench.data.hourly_series import load_hourly
from fbench.feature_builder import build_features
from fbench.models.base_forecast_model import REGISTRY
from fbench.report_generator import write_report
from fbench.quantile_scoring import add_skill, score
from fbench.mlflow_tracking import log_backtest

# Contender modules are imported as their plan tasks land; each import
# registers its model class as a side effect.
for mod in ("har_model", "sarima_model", "prophet_model",
            "xgboost_model", "nhits_model"):
    try:
        __import__(f"fbench.models.{mod}")
    except ImportError:
        pass

parser = argparse.ArgumentParser()
parser.add_argument("--models", default=",".join(sorted(REGISTRY)))
parser.add_argument("--stride", type=int, default=ORIGIN_STRIDE_DAYS)
parser.add_argument("--test-days", type=int, default=TEST_DAYS)
parser.add_argument("--no-report", action="store_true",
                    help="stop after writing the backtest parquet; skip "
                         "scoring, REPORT.md, and the MLflow log")
args = parser.parse_args()
names = args.models.split(",")

hourly = load_hourly()
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
run_config = {"stride": args.stride, "test_days": args.test_days,
              "horizon": HORIZON, "models": names, "origins": len(origins),
              # Dataset snapshot, so a later re-report describes the data
              # this backtest saw rather than the grown hourly file.
              "dataset_hours": len(hourly),
              "dataset_span_start": str(hourly.index.min()),
              "dataset_span_end": str(hourly.index.max()),
              "dataset_nan_hours": int(hourly["rv"].isna().sum())}
out.with_suffix(".json").write_text(json.dumps(run_config))
print(f"rows={len(res)} -> {out.name}  total {time.perf_counter()-t_all:.0f}s")

if not args.no_report:
    # Same chain run_vol_report.py applies to an existing parquet. It runs
    # exactly once per invocation, so one backtest logs once to
    # MLflow.
    scores = add_skill(score(res))
    report_path = write_report(scores, hourly, out)
    run_config.pop("models", None)  # param values must be scalars
    log_backtest(scores, out, run_config)
    print(f"report -> {report_path}")
    print(scores.groupby("model")["pinball_mean"].mean().sort_values())
