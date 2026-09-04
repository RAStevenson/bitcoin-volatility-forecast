"""Audit the evidence claim behind the live log by walking the commit
history of results/forecasts.csv and checking that every (origin, model)
group was committed before its first target hour completed. It reads git
history only, prints a line per group with its margin, and exits non-zero
if any group was late, so it can gate a build."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import argparse
import io
import subprocess

import pandas as pd

from fbench.config import ROOT

FORECAST_LOG = "results/forecasts.csv"

parser = argparse.ArgumentParser(
    description="Audit the live log's evidence claim: every forecast row "
                "was committed to git before its target hour completed. "
                "Walks the commit history of the forecast log, finds the "
                "first commit containing each (origin, model) group, and "
                "compares that commit's time against the group's earliest "
                "target completion (origin + 2h, since the first target "
                "hour is origin + 1h and completes an hour later).")
parser.parse_args()

log = subprocess.run(
    ["git", "log", "--reverse", "--format=%H %cI", "--", FORECAST_LOG],
    cwd=ROOT, capture_output=True, text=True, check=True)

first = {}  # (origin, model) -> (short sha, commit time)
for line in log.stdout.splitlines():
    if not line.strip():
        continue
    sha, stamp = line.split()
    committed = pd.Timestamp(stamp).tz_convert("UTC")
    show = subprocess.run(["git", "show", f"{sha}:{FORECAST_LOG}"],
                          cwd=ROOT, capture_output=True, text=True)
    if show.returncode != 0:
        continue  # log file absent at this commit
    df = pd.read_csv(io.StringIO(show.stdout),
                     usecols=["origin", "model"]).drop_duplicates()
    for origin, model in df.itertuples(index=False):
        first.setdefault((origin, model), (sha[:9], committed))

if not first:
    sys.exit("no committed forecast rows found")

by_origin = {}
for (origin, model), commit in first.items():
    by_origin.setdefault(origin, {}).setdefault(commit, []).append(model)

late = 0
for origin in sorted(by_origin):
    deadline = pd.Timestamp(origin) + pd.Timedelta(hours=2)
    for (sha, committed), models in sorted(by_origin[origin].items(),
                                           key=lambda kv: kv[0][1]):
        margin = (deadline - committed).total_seconds() / 60
        ok = committed < deadline
        late += 0 if ok else len(models)
        print(f"{'OK  ' if ok else 'LATE'} origin {origin}  "
              f"committed {committed} ({sha})  margin {margin:+.0f} min  "
              f"models: {len(models)}")

n = len(first)
print(f"\n{n} (origin, model) groups checked, {late} committed after "
      f"their first target hour completed")
sys.exit(1 if late else 0)
