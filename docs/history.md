# Project history

## Why the author's machine starts the daily run

The author's machine starts the run, with GitHub's own schedule as the
backup, because GitHub's documentation says a scheduled run can be
delayed under load. This was confirmed by experience, as the first
scheduled run launched by GitHub Actions, on 2026-09-27, started 4 hours
26 minutes late. Under the fixed 10:00 UTC origin, a run that late would
commit after the forecast's first target hours had passed and after the
US stock market had opened.

## The release of 2026-10-22

The models ran on the settings selected during their initial creation
until a release on 2026-10-22. That release changed three models'
settings and fixed two defects. Every forecast from 2026-10-23 on is
made under it. [LIVE.md][live] gives 2026-10-23 as the change date and
counts the scored days since. Forecasts made before the release stay in
the log as they were made.

### How the settings were chosen

The new settings were chosen by grid search, which scores every
combination of a few values for each setting. A candidate's score was
its mean pinball loss over 74 forecast origins at 10:00 UTC, one every
fifth day from 2024-07-31 to 2025-07-31. Those origins all fall before
the year the backtest scores, so the backtest is scored on days the
tuning never saw. XGBoost, N-HiTS, and Prophet each had eight
candidates, the old setting among them. XGBoost's trees are now six
levels deep instead of four, which scored 4.4% below the old setting's
loss on those origins. The candidate with the lowest loss also raised
the learning rate, the size of the correction each new tree makes. Its
loss was only about 0.1% lower, and its 90% band held the realized value
81% of the time against 84% for the adopted setting, so the release kept
the old rate. N-HiTS now trains for eight passes over its window instead
of three, which scored 1.3% below. Prophet's trend is now less free to
change slope, which scored 0.8% below. These are differences on one set
of 74 origins, with no interval computed.

SARIMAX was tried in four other forms, including a longer window and a
fixed daily cycle in place of its one-day lookback. Its existing form
scored best, so it is unchanged. Persistence, HAR, and their seasonal
versions were not tuned. They are kept fixed as benchmarks, since skill
is measured against persistence and HAR is the published standard
baseline. Every candidate's score is in [results/tuning/][tuning], and
`scripts/run_tune.py` reproduces them.

### The backtest before and after

The backtest scores the 365 days of history before 2026-08-05, with a
forecast origin every second day, 183 origins in all. It has been run
twice on those same days, once before the release and once after. The
first run used the original settings with origins at midnight UTC, and
its results are kept unchanged as the reference. Its winner, N-HiTS,
scored a mean pinball loss of 0.0959 on log volatility (lower is
better), averaged over forecast horizons of 1 to 24 hours ahead,
against 0.1180 for persistence on the same origins. The skill score
averaged over the same horizons is 0.186 (higher is better), meaning
its loss was 18.6% below persistence's on an average horizon. That
run's report, [results/REPORT_20260805.md][pinned-report], holds its
results table, figures, and dataset summary, unchanged since apart
from its two figure paths.

The second run, on 2026-10-22, used the release's settings and fixes,
with origins at 10:00 UTC, the hour the daily run forecasts from. N-HiTS
won again with a mean pinball loss of 0.0934, and XGBoost was close
behind at 0.0939. Persistence is the same model in both runs, so its
higher loss in the second, 0.1368 against 0.1180, comes from the origin
hour. Over the backtest year the 10:00 UTC hour was the quietest of the
day on average. Persistence forecasts that hour's level for all 24 hours
ahead, including the hours after the US stock market opens, which were
the most volatile. Skill is measured against persistence, so the second
run's skill scores are higher partly for that reason. The two runs
differ in both settings and origin hour, so their scores do not separate
the effect of the release from the effect of the hour. The second run is
the backtest the README reports, in [results/REPORT.md][report].

### The two defects

The first defect was that, until the release, the inputs of HAR,
seasonal HAR, and XGBoost stopped one hour before the origin hour.
Persistence forecasts from the origin hour itself, so it had an hour of
newer data than they did. In the backtest run before the release all
three lost to persistence one hour ahead. In the run after it, which
also moved its origins to 10:00 UTC, none did.

The second defect was in the daily record's score of each day's average.
It averaged each model's 24 hourly medians rather than their expected
values. For N-HiTS and XGBoost that average ran about 10% under the
realized one, even though realized hours fell above and below the
medians about equally often. The daily record now scores every day,
before and after the release, from expected values. From the release
on, FORECAST.md builds the day's average volatility from expected values
too. REVIEW.md scores each day before the release against the medians
that day's FORECAST.md printed.

[live]: ../results/LIVE.md
[tuning]: ../results/tuning/
[pinned-report]: ../results/REPORT_20260805.md
[report]: ../results/REPORT.md
