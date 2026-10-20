# Daily briefing prompt

This is the prompt a scheduled agent runs each morning after the daily
run. It checks that the run has committed and reports the committed
results. It computes nothing and edits nothing. The one thing it may run
is the pipeline itself, and only when the GitHub run has failed or never
started.

## Setting it up

Two roles use this prompt. A reader who only wants this repo's forecast
schedules it after 12:00 UTC and, if STEP 1 finds no commit for today,
reports that and stops. A reader never runs the pipeline. The forecast
record is this repo's commit history, and a local run would write only
to the reader's clone.

The owner of a daily run, on this repo or a fork of it, runs every step
of the prompt. The owner also schedules a separate daily job on their
machine that starts the run. The forecast origin is the 10:00
UTC hour, which closes at 11:00, and the run's commit has to land before
12:00 UTC to count as made before its first target hour ended. The run
is started from a machine you control because GitHub's own schedule is
best-effort and can fire hours late. The workflow keeps GitHub's
schedule at 11:15 and 11:45 UTC as the fallback for a day your machine
does not start it.

On Windows, this PowerShell command registers a Task Scheduler entry
that starts the run at 11:15 UTC every day. Replace OWNER with the
GitHub account that holds your copy of the repo.

```powershell
$t = New-ScheduledTaskTrigger -Daily -At 11:15; $t.StartBoundary = "2026-01-01T11:15:00Z"
Register-ScheduledTask -TaskName bitcoin-volatility-dispatch -Trigger $t -Settings (New-ScheduledTaskSettingsSet -StartWhenAvailable) -Action (New-ScheduledTaskAction -Execute (Get-Command gh).Source -Argument "workflow run daily-run.yml -f dry_run=false --repo OWNER/bitcoin-volatility-forecast")
```

On its own, `-At 11:15` would mean 11:15 local time. The second
statement replaces the start time with 11:15 UTC, which is what the Z
at its end means. Windows stores that time with a fixed offset from
UTC, so the run starts at 11:15 UTC on both sides of a daylight-saving
change. The machine needs the GitHub CLI signed in to an account that
can run the repo's workflows.

Then schedule this prompt for the owner at 11:30 UTC, after the run has
had time to commit and early enough that a local re-run in STEP 1 still
lands before 12:00 UTC. A Claude Code scheduled task is how the author
runs it. In the Claude desktop app, ask Claude to schedule a daily task
at that time and give it the text below the line as the prompt. The app
runs it in a fresh session each day, and the briefing arrives as that
session's reply. The app schedules in local time, so the task moves an
hour against UTC at each daylight-saving change. The author's task runs
at 6:30 in the morning in Chicago, which is 11:30 UTC in summer and
12:30 UTC in winter. In winter a local re-run therefore commits after
12:00 UTC, and the next run lists that day as late in `results/LIVE.md`.

Any other agent that can run shell commands and read files works the
same way on its own scheduler, with the text below the line as its
instructions. Without an agent, pull the repo and read
`results/FORECAST.md`, `results/REVIEW.md`, and `results/LIVE.md` in
that order. STEP 2 is a reading order, not a computation.

The machine that runs this prompt for the owner needs the project's
virtual environment built, because STEP 1 may run the pipeline there.
Replace "the repo's directory" in the prompt with your clone's path.

---

STEP 1 - CHECK THAT THE RUN LANDED. In the repo's directory, execute
exactly:

```
git pull --ff-only
git log -30 --format=%s
```

If any line starts with "Daily run <today's date in UTC, YYYY-MM-DD>",
the run has landed: go to STEP 2. It need not be the newest commit,
since other work may have been pushed after the run. If no line does,
a reader reports in one line that today's commit has not landed and
stops. The owner executes:

```
gh run list --workflow daily-run.yml --limit 3
```

and act on the newest run listed for today:

- Queued or in progress: wait two minutes (`sleep 120` as one Bash
  command with run_in_background set to true and timeout 600000) and
  repeat STEP 1, at most ten times, twenty minutes in all. After the
  tenth, report in one line that the run is still in progress and stop.
  GitHub's own schedule may also fire meanwhile; the workflow skips a
  second start once the day has committed.
- Failed, or no run for today at all: run the pipeline on this machine
  with the project's own Python, then repeat the pull and the log check
  once.

```
.venv/Scripts/python.exe scripts/run_daily.py
```

The script commits and pushes for itself. If it commits after 12:00
UTC, the next run's audit lists the day in results/LIVE.md with what
started it and when; do not try to hide or repair that. If the local
run fails too, report in one line the stage it stopped at (the last
line starting with [daily] before the error) and the error's final
line, and stop.

Report in one line how the run landed: from GitHub started on request
(trigger workflow_dispatch), from GitHub's own schedule (trigger
schedule), or locally (trigger local), with the start time. Both are in
the commit message, after "trigger".

STEP 2 - BRIEF, in this order. Plain prose, no emoji, ASCII only.

Lead with the forecast: relay results/FORECAST.md essentially
verbatim. Its first line (for example "quiet and falling"), the
expected level and where it sits against the past year, the expected
high-volatility hours, and the loudest and calmest local hours.

Then yesterday in review, briefly, from results/REVIEW.md: the result
(on target, too low, too high) with the forecast average, the realized
average and the ratio, and the 90% band line as written. Add the
table of the largest hourly errors only when the result was too low or
too high. Leave out the rest of the file, including the sentence that
defines on target and the section on the daily forecast's own claims.
Every number comes from the file; add no diagnosis the file does not
contain.

Then, briefly, system health:

- Whether today's run was clean, and how many consecutive days have
  run.
- Yesterday's scoring: rows resolved, the leading model in the daily
  record with its pinball loss, and any change of leader since the
  previous briefing.

If a scoring anomaly or a failed step exists, it moves to the top,
above the forecast.

HARD RULES:

- Never start the GitHub workflow. The owner's scheduler starts it, and
  GitHub's own schedule is the fallback.
- Never hand-edit anything under data/ or results/. The script produces
  every number.
- Never commit or push by hand. The only commit this task may cause is
  the one scripts/run_daily.py makes when it runs locally in STEP 1.
- Never predict or fabricate a pending result; report only what the
  files say.
- Do not fetch external URLs.
- The forecast describes volatility only. Never add commentary about
  price direction, trade ideas, or market calls that the files do not
  contain.
