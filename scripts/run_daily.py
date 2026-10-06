"""Run the daily loop end to end, extending the committed hourly
realized volatility series with the minutes since its last hour,
resolving the forecasts whose target hour has closed, logging a fresh 24-hour forecast for every
registered model, auditing the commit timing of earlier forecasts,
regenerating the three reports (the review with the daily forecast's claims
scored), and committing and pushing the result."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import argparse
import os
import subprocess
import traceback

import pandas as pd
import requests

# Import all model modules so the registry is complete for the daily fits.
import fbench.models.har_model
import fbench.models.nhits_model  # joined 2026-08-06 after leading the backtest
import fbench.models.persistence_model
import fbench.models.prophet_model
import fbench.models.sarima_model
import fbench.models.xgboost_model  # noqa: F401
from fbench import daily_run
from fbench.commit_timing import first_commits, late_groups
from fbench.daily_forecast_generator import write_daily_forecast
from fbench.data.hourly_series import update_hourly
from fbench.feature_builder import build_features
from fbench.harness_config import ROOT
from fbench.review_generator import write_review

TRACKED_PATHS = ("data/hourly_rv.csv",
                 "results/forecasts.csv", "results/evaluation.csv",
                 "results/LIVE.md", "results/FORECAST.md",
                 "results/REVIEW.md",
                 "results/figures/fig_live_daily.png")


def _audit():
    """Runs the commit-timing audit over the forecast log's history and
    returns the late forecast days. If the audit fails it prints the
    full error and returns None, and the run carries on: the day's
    forecast matters more than the audit, which the next run repeats,
    and LIVE.md then points to scripts/run_verify_timing.py instead of
    stating a result."""
    try:
        return late_groups(first_commits(ROOT))
    except Exception as error:
        traceback.print_exc()
        # first_commits captures git's output, so git's own message has
        # to be printed here or it is lost.
        if isinstance(error, subprocess.CalledProcessError) and error.stderr:
            print(error.stderr.strip(), file=sys.stderr)
        print("[daily] The timing audit failed (full error above). The run "
              "continues, and LIVE.md will point to "
              "scripts/run_verify_timing.py instead of stating the audit's "
              "result.", file=sys.stderr, flush=True)
        return None


def _commit_push(commit_message, no_commit, no_push):
    """Commits the extended hourly series, the logs, the reports and
    the live figure with commit_message, pushing when an origin remote
    is configured and no_push is false; with no_commit it returns before
    staging anything. A failed push stops the run with a message saying
    the commit was made but GitHub does not have it. Committing happens
    before the logged target hours close, which is what makes the
    forecast log pre-outcome evidence. A second run on the same day
    would normally stage newly resolved rows and a refreshed forecast
    file, so what stops one is the workflow's skip guard, not this
    function; the nothing-staged return below only covers a rerun with
    no new data."""
    if no_commit:
        print("  --no-commit: files written, nothing committed")
        return
    tracked_paths = [path for path in TRACKED_PATHS if (ROOT / path).exists()]
    subprocess.run(["git", "add", *tracked_paths], cwd=ROOT, check=True)
    staged_check = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT)
    if staged_check.returncode == 0:
        print("  nothing new to commit (already ran today)")
        return
    subprocess.run(["git", "commit", "-m", commit_message], cwd=ROOT, check=True)
    remotes = subprocess.run(["git", "remote"], cwd=ROOT,
                             capture_output=True, text=True).stdout.split()
    if "origin" in remotes and not no_push:
        try:
            subprocess.run(["git", "push", "origin", "HEAD"], cwd=ROOT,
                           check=True)
        except subprocess.CalledProcessError:
            traceback.print_exc()
            sys.exit("[daily] The day's commit was made but the push failed "
                     "(git's message is above), so GitHub does not have "
                     "today's forecast.")
        print("  committed and pushed")
    elif no_push:
        print("  committed; push skipped (--no-push)")
    else:
        print("  committed; no remote configured, push skipped")


def main():
    """Runs every stage of the daily loop in order, printing a plain line
    before each, and commits and pushes the result unless told not to."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-push", action="store_true",
                        help="commit the run's files locally and do not push")
    parser.add_argument("--no-commit", action="store_true",
                        help="write every file and commit nothing (implies --no-push)")
    args = parser.parse_args()

    # Recorded in the day's commit message so the timing audit can say
    # what started a late run and when. GitHub sets GITHUB_EVENT_NAME to
    # "schedule" or "workflow_dispatch"; a run on a person's machine has
    # neither and is recorded as local.
    started = pd.Timestamp.now(tz="UTC")
    trigger = os.environ.get("GITHUB_EVENT_NAME", "local")

    print("[daily] updating the hourly series from Coinbase", flush=True)
    try:
        hourly, last_close, n_minutes_fetched = update_hourly()
    except requests.RequestException:
        traceback.print_exc()
        sys.exit("[daily] The Coinbase request failed after its retries (full "
                 "error above). Nothing was written or committed.")
    print(f"  minutes fetched: {n_minutes_fetched}; series through {hourly.index[-1]}")
    print("[daily] scoring earlier forecasts whose hours have ended", flush=True)
    n_rows_resolved = daily_run.score_due(hourly)
    print(f"  rows resolved: {n_rows_resolved}")

    features = build_features(hourly)
    # The origin is the same clock hour every day (see fixed_origin),
    # never the hour the run happens to start in, so a late start changes
    # nothing about which data the models see.
    print("[daily] choosing the origin hour", flush=True)
    origin = daily_run.fixed_origin(hourly)
    print("[daily] fitting every model and logging its 24-hour forecast", flush=True)
    n_rows_logged = daily_run.log_forecasts(features, origin)
    print(f"  forecast rows logged: {n_rows_logged} (origin {origin})")

    print("[daily] auditing the commit timing of earlier forecasts", flush=True)
    late_days = _audit()
    print(f"  late forecast days: {'not audited' if late_days is None else len(late_days)}")
    print("[daily] writing LIVE.md", flush=True)
    daily_run.write_live_report(late=late_days)
    print("[daily] writing FORECAST.md", flush=True)
    write_daily_forecast(hourly, last_price=last_close)
    print("[daily] writing REVIEW.md", flush=True)
    write_review(hourly)

    print("[daily] committing and pushing", flush=True)
    day = pd.Timestamp.now(tz="UTC").date()
    commit_message = (f"Daily run {day}: {n_rows_logged} forecast rows logged, "
                      f"{n_rows_resolved} resolved; origin {origin:%H:%M} UTC; "
                      f"trigger {trigger}, started {started:%H:%M} UTC")
    _commit_push(commit_message, args.no_commit, args.no_push)
    print("[daily] done")


if __name__ == "__main__":
    main()
