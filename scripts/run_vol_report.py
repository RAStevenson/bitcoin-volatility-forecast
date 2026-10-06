"""Rebuild results/REPORT.md and its figures from an existing backtest
parquet, the newest in results/backtest/ unless --results names one, and log that
backtest to MLflow again. It re-reports a finished run rather than
running one, and the Dataset section is pinned by the parquet's json
sidecar whenever that carries the snapshot keys."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import argparse
import json

import pandas as pd

from fbench.data.hourly_series import load_hourly
from fbench.harness_config import RESULTS_DIR
from fbench.mlflow_tracking import log_backtest
from fbench.quantile_scoring import add_skill, score
from fbench.report_generator import write_report

parser = argparse.ArgumentParser()
parser.add_argument("--results", default=None,
                    help="backtest parquet; default: newest in "
                         "results/backtest/")
args = parser.parse_args()

if args.results:
    results_path = Path(args.results)
else:
    candidates = sorted((RESULTS_DIR / "backtest").glob("backtest_*.parquet"))
    if not candidates:
        sys.exit("no backtest parquet in results/backtest/")
    results_path = candidates[-1]

results = pd.read_parquet(results_path)
hourly = load_hourly()
scores = add_skill(score(results))

run_config = json.loads(results_path.with_suffix(".json").read_text())
stat_keys = ("dataset_hours", "dataset_span_start", "dataset_span_end",
             "dataset_nan_hours")
dataset_stats = ({key: run_config[key] for key in stat_keys}
                 if all(key in run_config for key in stat_keys) else None)
report_path = write_report(scores, hourly, results_path,
                           dataset_stats=dataset_stats)
run_config.pop("models", None)  # param values must be scalars
log_backtest(scores, results_path, run_config)
print(f"report -> {report_path}")
print(scores.groupby("model")["pinball_mean"].mean().sort_values())
