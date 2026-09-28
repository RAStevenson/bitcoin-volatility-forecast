# Daily briefing prompt

The prompt a scheduled agent runs each morning. It starts the GitHub
Actions run, waits for it, and reports the committed results. It
computes nothing and edits nothing. The one thing it may run is the
pipeline itself, and only when the GitHub run has failed or never
started.

## Setting it up

Two roles use this prompt. The owner of a daily run, on this repo or
a fork of it, schedules it for 11:15 UTC or any earlier local time,
and runs every step. The first step waits for 11:15 UTC, which is how
a local schedule survives clock changes without being moved. A reader
who only wants this repo's forecast schedules it after 12:00 UTC,
skips STEP 1, and, if STEP 2 finds no commit for today, reports that
and stops. A reader never runs the pipeline. The forecast record is
this repo's commit history, and a local run would write only to the
reader's clone.

For the owner, the forecast origin is the 10:00 UTC hour,
which closes at 11:00, and the run's commit has to land before 12:00
UTC to count as made before its first target hour ended. The run is
started from a machine you control because GitHub's own schedule is
best-effort and can fire hours late. The workflow keeps GitHub's
schedule at 11:15 and 11:45 UTC as the fallback for a day this task
does not run. Any of these works:

- **A Claude Code scheduled task**, which is how the author runs it. In
  the Claude desktop app, ask Claude to schedule a daily task at that
  time and give it the text below the line as the prompt. The app
  stores the task as a Markdown file under `~/.claude/scheduled-tasks/`
  with a name and a one-line description at the top, and runs it in a
  fresh session each day. The briefing arrives as that session's reply.
- **Any other agent** that can run shell commands and read files, on
  its own scheduler, with the same text as its instructions.
- **No agent.** Start the run with the first command below, wait for
  it, pull, and read `results/REVIEW.md`, `results/FORECAST.md`, and
  `results/LIVE.md` in that order. Step 3 is a reading order,
  not a computation.

The machine needs the GitHub CLI signed in to the repo and the
project's virtual environment built. Replace "the repo's directory"
with your clone's path.

---

STEP 1 - START THE RUN. Read the clock in UTC with
`(Get-Date).ToUniversalTime()`. If it is before 11:15 UTC, wait until
11:15 UTC, sleeping in stretches of at most 100 seconds
(`Start-Sleep -Seconds 100`), since a longer sleep outruns the shell
tool's timeout. The origin hour closes at 11:00. A run started before
then has nothing to forecast and fails on purpose. Then, in the repo's
directory, execute exactly:

```
gh workflow run daily-run.yml -f dry_run=false
```

Run that command once and do not retry it. A second start the same
day, from a retry, from a second session of this task, or from
GitHub's own schedule, is harmless: the workflow checks the branch tip
and skips once the day has committed.

Then wait five minutes. The run takes about three and a half.

STEP 2 - CHECK THAT IT LANDED. Execute exactly:

```
git pull --ff-only
git log -30 --format=%s
```

If any line starts with "Daily run <today's date in UTC, YYYY-MM-DD>",
the run has landed: go to STEP 3. It need not be the newest commit,
since other work may have been pushed after the run. If no line does,
a reader reports in one line that today's commit has not landed and
stops. The owner executes:

```
gh run list --workflow daily-run.yml --limit 3
```

and act on the newest run listed for today:

- Queued or in progress: wait two minutes and repeat STEP 2, for up to
  twenty minutes in all. After twenty minutes, report in one line that
  the run is still in progress and stop. GitHub's own schedule may also
  fire meanwhile; the workflow skips a second start once the day has
  committed.
- Failed, or no run for today at all: run the pipeline on this machine
  with the project's own Python, then repeat the pull and the log check
  once.

```
.venv/Scripts/python.exe scripts/run_daily.py
```

The script commits and pushes for itself. If it commits after 12:00
UTC, the next run's audit lists the day in results/LIVE.md with what
started it and when; do not try to hide or repair that. If the local
run fails too, report its failing step in one line and stop.

Report in one line how the run landed: from GitHub started by this
task, from GitHub's own schedule, or locally, with the start time. Both
are in the commit message, after "trigger".

STEP 3 - BRIEF, in this order. Plain prose, no emoji, ASCII only.

Lead with yesterday in review: relay results/REVIEW.md essentially
verbatim. The result (on target, too low, too high), the forecast
average against the realized average and the ratio, the hours inside
the 90% band, where the day ranks among scored days, and the table of
the largest hourly errors. Every number comes from the file; add no
diagnosis the file does not contain.

Then the forecast: relay results/FORECAST.md essentially verbatim. Its
first line (for example "quiet and falling"), the expected level and
where it sits against the past year, the expected high-volatility
hours, and the loudest and calmest local hours. Review first, then
forecast, always.

Then, briefly, system health:

- Whether today's run was clean, and how many consecutive days have
  run.
- Yesterday's scoring: rows resolved, the leading model in the daily
  record with its pinball loss, and any change of leader since the
  previous briefing.
- Calibration: relay the "calibration check" line from results/LIVE.md
  verbatim in one clause. The script computes the result itself. Raise
  it as an alert only if that line begins "The calibration check
  flags". While it says "stays inactive", "passes", or "found no model
  with enough scored days", it is one clause and never an alert. That
  holds when it names a model as pending part way through the three
  days; a pending model is worth one sentence, not a heading. Never apply a threshold to the raw cov90 column
  yourself. Its day-to-day noise is larger than the gaps between
  models. Reading the column as exact is the mistake the check was rebuilt on
  2026-08-24 to stop making (see the README, The calibration check).

If a scoring anomaly or a failed step exists, it moves to the top,
above the forecast.

HARD RULES:

- Never hand-edit anything under data/ or results/. The script produces
  every number.
- Never commit or push by hand. The only commit this task may cause is
  the one scripts/run_daily.py makes when it runs locally in STEP 2.
- Never predict or fabricate a pending result; report only what the
  files say.
- Do not fetch external URLs.
- The forecast describes volatility only. Never add commentary about
  price direction, trade ideas, or market calls that the files do not
  contain.
