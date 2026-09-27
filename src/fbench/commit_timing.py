"""Audit of the forecast log's timing claim against git history, the
claim that every forecast row was committed before its first target hour
ended: for every (origin, model) forecast group in results/forecasts.csv,
the commit that first added it, and which groups were first committed
after their first target hour completed. The daily run does this before
writing LIVE.md so that file states its exceptions instead of a blanket
claim, and scripts/run_verify_timing.py runs it as a standalone check."""
import re
import subprocess

import pandas as pd

FORECAST_LOG = "results/forecasts.csv"
COMMIT_MARK = "@@commit "

# Why a forecast day was committed late, keyed by its origin date, one
# full sentence for LIVE.md to print after the delay. A late day with no
# entry here is listed with no reason, never a guessed one.
LATE_COMMIT_REASONS = {
    "2026-09-03": "The machine that ran the daily job had an unplanned "
                  "restart.",
}


def parse_log(text):
    """Map each (origin, model) group to the (short sha, commit time,
    subject) of the first commit whose diff added one of its rows, from
    the output of `git log --reverse -p --unified=0` with a COMMIT_MARK
    format line carrying the hash, the time, and the subject.
    Only added lines are read, so the cost grows with what each commit
    changed rather than with the size of the file. A group re-added by a
    later commit (the log was rewritten whole before 2026-09-10) keeps
    its first commit."""
    first, current = {}, None
    for raw in text.splitlines():
        line = raw.rstrip("\r")
        if line.startswith(COMMIT_MARK):
            sha, stamp, *subject = line[len(COMMIT_MARK):].split(maxsplit=2)
            current = (sha[:9], pd.Timestamp(stamp).tz_convert("UTC"),
                       subject[0] if subject else "")
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
        ["git", "log", "--reverse", f"--format={COMMIT_MARK}%H %cI %s", "-p",
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
    for (origin, _model), (sha, committed, subject) in first.items():
        grouped.setdefault((origin, sha, committed, subject), 0)
        grouped[(origin, sha, committed, subject)] += 1
    late = []
    for (origin, sha, committed, subject), n in sorted(grouped.items()):
        deadline = pd.Timestamp(origin) + pd.Timedelta(hours=2)
        if committed >= deadline:
            late.append({"origin": pd.Timestamp(origin), "sha": sha,
                         "committed": committed, "models": n,
                         "minutes_late": (committed - deadline).total_seconds() / 60,
                         "subject": subject})
    return late


_TRIGGER_WORDS = {
    "schedule": "GitHub's scheduled trigger",
    "workflow_dispatch": "a dispatch from the author's machine",
    "local": "a run on the author's machine",
}


def run_note(subject):
    """One sentence on what started the run that made a commit and when,
    read from the trigger and start time the daily run writes into its
    commit subject since 2026-09-27, or None for a subject without them.
    A late day with no entry in LATE_COMMIT_REASONS gets this sentence,
    so a delayed trigger explains itself in LIVE.md."""
    m = re.search(r"trigger (\S+), started (\d\d:\d\d) UTC", subject or "")
    if not m:
        return None
    what = _TRIGGER_WORDS.get(m.group(1), m.group(1))
    return f"The run that committed it was started by {what} at {m.group(2)} UTC."
