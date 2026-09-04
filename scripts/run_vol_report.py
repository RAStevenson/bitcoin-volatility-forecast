"""Rebuild results/REPORT.md and its figures from an existing backtest
parquet, the newest in results/ unless --results names one, and log that
tournament to MLflow again. It re-reports a finished run rather than
running one, and the Dataset section is pinned by the parquet's json
sidecar whenever that carries the snapshot keys."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import argparse
import json

import pandas as pd

from fbench.harness_config import DATA_DIR, RESULTS_DIR
from fbench.report_generator import write_report
from fbench.quantile_scoring import add_skill, score
from fbench.mlflow_tracking import log_tournament

parser = argparse.ArgumentParser()
parser.add_argument("--results", default=None,
                    help="backtest parquet; default: newest in results/")
args = parser.parse_args()

if args.results:
    results_path = Path(args.results)
else:
    candidates = sorted(RESULTS_DIR.glob("backtest_*.parquet"))
    if not candidates:
        sys.exit("no backtest parquet in results/")
    results_path = candidates[-1]

results = pd.read_parquet(results_path)
hourly = pd.read_parquet(DATA_DIR / "hourly_rv.parquet")
scores = add_skill(score(results))

run_config = json.loads(results_path.with_suffix(".json").read_text())
stat_keys = ("dataset_hours", "dataset_span_start", "dataset_span_end",
             "dataset_nan_hours")
dataset_stats = ({k: run_config[k] for k in stat_keys}
                 if all(k in run_config for k in stat_keys) else None)
report_path = write_report(scores, hourly, results_path,
                           dataset_stats=dataset_stats)
run_config.pop("models", None)  # param values must be scalars
log_tournament(scores, results_path, run_config)
print(f"report -> {report_path}")
print(scores.groupby("model")["pinball_mean"].mean().sort_values())
