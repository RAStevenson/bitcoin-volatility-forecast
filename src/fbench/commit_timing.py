"""Audit of the live log's evidence claim against git history: for every
(origin, model) forecast group in results/forecasts.csv, the commit that
first added it, and which groups were first committed after their first
target hour completed. The daily loop runs it before writing LIVE.md so
the scoreboard states its exceptions instead of a blanket claim, and
scripts/run_verify_timing.py runs it as a standalone check."""
import subprocess

import pandas as pd

FORECAST_LOG = "results/forecasts.csv"
COMMIT_MARK = "@@commit "


def parse_log(text):
    """Map each (origin, model) group to the (short sha, commit time) of
    the first commit whose diff added one of its rows, from the output of
    `git log --reverse -p --unified=0` with a COMMIT_MARK format line.
    Only added lines are read, so the cost grows with what each commit
    changed rather than with the size of the file. A group re-added by a
    later commit (the log was rewritten whole before 2026-09-10) keeps
    its first commit."""
    first, current = {}, None
    for raw in text.splitlines():
        line = raw.rstrip("\r")
        if line.startswith(COMMIT_MARK):
            sha, stamp = line[len(COMMIT_MARK):].split()
            current = (sha[:9], pd.Timestamp(stamp).tz_convert("UTC"))
        elif (current and line.startswith("+") and not line.startswith("+++")
              and not line.startswith("+origin,")):
            parts = line[1:].split(",")
            if len(parts) >= 4:
                first.setdefault((parts[0], parts[3]), current)
    return first


def first_commits(root, path=FORECAST_LOG):
    """Run git in root and return parse_log's mapping for the forecast log
    at path, covering every commit that touched it."""
    out = subprocess.run(
        ["git", "log", "--reverse", f"--format={COMMIT_MARK}%H %cI", "-p",
         "--unified=0", "--", path],
        cwd=root, capture_output=True, text=True, check=True)
    return parse_log(out.stdout)


def late_groups(first):
    """The forecast days whose rows were first committed after their first
    target hour completed, one dict per (origin, commit) with the minutes
    late and the number of models, oldest first. The first target hour
    starts an hour after the origin and completes an hour later, so the
    deadline is the origin plus two hours; a group committed before it
    was committed before every one of its target hours completed."""
    grouped = {}
    for (origin, _model), (sha, committed) in first.items():
        grouped.setdefault((origin, sha, committed), 0)
        grouped[(origin, sha, committed)] += 1
    late = []
    for (origin, sha, committed), n in sorted(grouped.items()):
        deadline = pd.Timestamp(origin) + pd.Timedelta(hours=2)
        if committed >= deadline:
            late.append({"origin": pd.Timestamp(origin), "sha": sha,
                         "committed": committed, "models": n,
                         "minutes_late": (committed - deadline).total_seconds() / 60})
    return late
