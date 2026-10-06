"""Run the model backtest over data/hourly_rv.csv and save the
scored rows as results/backtest/backtest_<date>.parquet with a json sidecar
holding the run's settings and a snapshot of the dataset it saw. Unless
--no-report is given it also writes results/REPORT.md with its two
figures and logs the backtest to MLflow."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import argparse
import contextlib
import json
import time

import pandas as pd

import fbench.models.persistence_model  # noqa: F401  (registers baselines)
from fbench.data.hourly_series import load_hourly
from fbench.feature_builder import build_features
from fbench.harness_config import HORIZON, ORIGIN_STRIDE_DAYS, RESULTS_DIR, TEST_DAYS
from fbench.mlflow_tracking import log_backtest
from fbench.models.base_forecast_model import REGISTRY
from fbench.quantile_scoring import add_skill, score
from fbench.report_generator import write_report
from fbench.rolling_backtest import make_origins, run_backtest

# Each model module is imported here because the import is what
# registers its model class.
for module_name in ("har_model", "sarima_model", "prophet_model",
                    "xgboost_model", "nhits_model"):
    with contextlib.suppress(ImportError):
        __import__(f"fbench.models.{module_name}")

parser = argparse.ArgumentParser()
parser.add_argument("--models", default=",".join(sorted(REGISTRY)))
parser.add_argument("--stride", type=int, default=ORIGIN_STRIDE_DAYS)
parser.add_argument("--test-days", type=int, default=TEST_DAYS)
parser.add_argument("--no-report", action="store_true",
                    help="stop after writing the backtest parquet; skip "
                         "scoring, REPORT.md, and the MLflow log")
args = parser.parse_args()
model_names = args.models.split(",")

hourly = load_hourly()
features = build_features(hourly)
origins = make_origins(features.index, args.test_days, args.stride)
print(f"models={model_names} origins={len(origins)}", flush=True)

results_per_model, run_start_time = [], time.perf_counter()
for model_name in model_names:
    model_start_time = time.perf_counter()
    results_per_model.append(run_backtest(features, [model_name], origins))
    print(f"{model_name}: {time.perf_counter() - model_start_time:.1f}s", flush=True)
results = pd.concat(results_per_model, ignore_index=True)

(RESULTS_DIR / "backtest").mkdir(parents=True, exist_ok=True)
date_stamp = pd.Timestamp.now(tz="UTC").strftime("%Y%m%d")
results_path = RESULTS_DIR / "backtest" / f"backtest_{date_stamp}.parquet"
results.to_parquet(results_path, index=False)
run_config = {"stride": args.stride, "test_days": args.test_days,
              "horizon": HORIZON, "models": model_names, "origins": len(origins),
              # Dataset snapshot, so a later re-report describes the data
              # this backtest saw rather than the grown hourly file.
              "dataset_hours": len(hourly),
              "dataset_span_start": str(hourly.index.min()),
              "dataset_span_end": str(hourly.index.max()),
              "dataset_nan_hours": int(hourly["rv"].isna().sum())}
results_path.with_suffix(".json").write_text(json.dumps(run_config))
print(f"rows={len(results)} -> {results_path.name}  "
      f"total {time.perf_counter() - run_start_time:.0f}s")

if not args.no_report:
    # Same chain run_vol_report.py applies to an existing parquet. It runs
    # exactly once per invocation, so one backtest logs once to
    # MLflow.
    scores = add_skill(score(results))
    report_path = write_report(scores, hourly, results_path)
    run_config.pop("models", None)  # param values must be scalars
    log_backtest(scores, results_path, run_config)
    print(f"report -> {report_path}")
    print(scores.groupby("model")["pinball_mean"].mean().sort_values())
