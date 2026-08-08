import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import argparse
import json

import pandas as pd

from fbench.config import DATA_DIR, RESULTS_DIR
from fbench.report import write_report
from fbench.scoring import add_skill, score
from fbench.tracking import log_tournament

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

report_path = write_report(scores, hourly, results_path)
run_config = json.loads(results_path.with_suffix(".json").read_text())
run_config.pop("models", None)  # param values must be scalars
log_tournament(scores, results_path, run_config)
print(f"report -> {report_path}")
print(scores.groupby("model")["pinball_mean"].mean().sort_values())
