# Daily briefing prompt

The prompt a scheduled agent runs each morning after the GitHub Actions
run. It
reads the committed results and reports them; it computes nothing and
edits nothing. Schedule it an hour after the daily run's time (the
workflow runs at 11:12 UTC, with a retry at 11:42) with any agent that can run shell
commands and read files, or read the three files yourself.

---

STEP 1 - PULL AND CHECK. In the repo's directory, execute exactly:

```
git pull --ff-only
git log -1 --format=%s
```

If the latest commit message starts with "Daily run <today's date in
UTC, YYYY-MM-DD>", the run has landed: go to STEP 2. If it does
not, the GitHub Actions run has not committed today. Do not run the
pipeline yourself. Report in one line that the GitHub Actions run has not
landed, with the latest commit's message and date, and stop. The
workflow's own log on GitHub is where the failure is read.

STEP 2 - BRIEF, in this order. Plain prose, no emoji, ASCII only.

Lead with yesterday in review: relay results/REVIEW.md essentially
verbatim. The result (on target, too low, too high), the forecast
average against the realized average and the ratio, the hours inside
the 90% band, where the day ranks among scored days, and the table of
the largest hourly misses. Every number comes from the file; add no
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
- Never commit or push anything.
- Never predict or fabricate a pending result; report only what the
  files say.
- Do not fetch external URLs.
- The forecast describes volatility only. Never add commentary about
  price direction, trade ideas, or market calls that the files do not
  contain.
