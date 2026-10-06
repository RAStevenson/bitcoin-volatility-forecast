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


def main():
    """Runs the timing audit, prints one line per forecast day with its
    margin, and exits 1 if any day was committed late. The parser takes no
    arguments; it exists so --help prints what the audit checks."""
    parser = argparse.ArgumentParser(
        description="Audit the forecast log's timing claim: every forecast row "
                    "was committed to git before its target hour completed. "
                    "Finds the first commit that added each (origin, model) "
                    "group and compares that commit's time against the group's "
                    "earliest target completion (origin + 2h, since the first "
                    "target hour is origin + 1h and completes an hour later).")
    parser.parse_args()

    first_commit_by_group = first_commits(ROOT)
    if not first_commit_by_group:
        sys.exit("no committed forecast rows found")

    models_per_day = {}
    for (origin, _model), (commit_sha, committed_at, _subject) in first_commit_by_group.items():
        models_per_day.setdefault((origin, commit_sha, committed_at), 0)
        models_per_day[(origin, commit_sha, committed_at)] += 1
    for (origin, commit_sha, committed_at), n_models in sorted(models_per_day.items()):
        margin_minutes = ((pd.Timestamp(origin) + pd.Timedelta(hours=2)) - committed_at
                          ).total_seconds() / 60
        print(f"{'OK  ' if margin_minutes > 0 else 'LATE'} origin {origin}  "
              f"committed {committed_at} ({commit_sha})  margin {margin_minutes:+.0f} min  "
              f"models: {n_models}")

    late_days = late_groups(first_commit_by_group)
    n_late_groups = sum(late_day["models"] for late_day in late_days)
    print(f"\n{len(first_commit_by_group)} (origin, model) groups checked, "
          f"{n_late_groups} committed after their first target hour completed")
    sys.exit(1 if late_days else 0)


if __name__ == "__main__":
    main()
