"""Audit the timing claim behind the forecast log, that every forecast row
was committed before its first target hour ended, by walking the commit
history of results/forecasts.csv and checking every (origin, model)
group. It reads git history only, prints a line per forecast day with its
margin, and exits non-zero if any group was late, so a CI job can fail on
it. The daily run runs the same audit and prints its exceptions in
LIVE.md."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import argparse

import pandas as pd

from fbench.commit_timing import first_commits, late_groups
from fbench.harness_config import ROOT

parser = argparse.ArgumentParser(
    description="Audit the forecast log's timing claim: every forecast row "
                "was committed to git before its target hour completed. "
                "Finds the first commit that added each (origin, model) "
                "group and compares that commit's time against the group's "
                "earliest target completion (origin + 2h, since the first "
                "target hour is origin + 1h and completes an hour later).")
parser.parse_args()

first = first_commits(ROOT)
if not first:
    sys.exit("no committed forecast rows found")

days = {}
for (origin, _model), (sha, committed, _subject) in first.items():
    days.setdefault((origin, sha, committed), 0)
    days[(origin, sha, committed)] += 1
for (origin, sha, committed), n_models in sorted(days.items()):
    margin = ((pd.Timestamp(origin) + pd.Timedelta(hours=2)) - committed
              ).total_seconds() / 60
    print(f"{'OK  ' if margin > 0 else 'LATE'} origin {origin}  "
          f"committed {committed} ({sha})  margin {margin:+.0f} min  "
          f"models: {n_models}")

late = late_groups(first)
n_late = sum(group["models"] for group in late)
print(f"\n{len(first)} (origin, model) groups checked, {n_late} committed "
      f"after their first target hour completed")
sys.exit(1 if late else 0)
