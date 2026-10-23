"""Audit the timing claim behind the forecast log, that every forecast row
was committed before its first target hour ended, by walking the commit
history of results/forecasts.csv and checking every (origin, model)
group. It reads git history only, prints a line per forecast day with its
margin and, for a late day, the reason TIMING.md gives for it. It exits
non-zero only if a late day has no reason, meaning neither an entry in
LATE_COMMIT_REASONS nor a trigger and start time in its commit subject,
so a CI job fails on a late commit nothing accounts for rather than on
every day already listed in TIMING.md."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import argparse

import pandas as pd

from bitcoin_volatility_forecast.commit_timing import first_commits, late_groups, late_reason
from bitcoin_volatility_forecast.forecast_settings import ROOT


def main():
    """Runs the timing audit, prints one line per forecast day with its
    margin and each late day's reason, and exits 1 if any late day has no
    reason. The parser takes no arguments; it exists so --help prints what
    the audit checks."""
    parser = argparse.ArgumentParser(
        description="Audit the forecast log's timing claim: every forecast row "
                    "was committed to git before its target hour completed. "
                    "Finds the first commit that added each (origin, model) "
                    "group and compares that commit's time against the group's "
                    "earliest target completion (origin + 2h, since the first "
                    "target hour is origin + 1h and completes an hour later). "
                    "Exits 1 only if a late day has no recorded reason and no "
                    "trigger in its commit subject.")
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
    unexplained_days = []
    for late_day in late_days:
        reason = late_reason(late_day)
        print(f"  late {late_day['origin']:%Y-%m-%d}: "
              f"{reason or 'NO REASON RECORDED'}")
        if reason is None:
            unexplained_days.append(late_day)
    print(f"{len(unexplained_days)} late days with no recorded reason")
    sys.exit(1 if unexplained_days else 0)


if __name__ == "__main__":
    main()
