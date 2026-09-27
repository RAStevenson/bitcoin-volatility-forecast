# bitcoin-volatility-forecast

This repo publishes a daily forecast of how much the price of BTC-USD
(Bitcoin priced in US dollars) will fluctuate over the next 24 hours,
and holds the code that scores that forecast against reality. The
size of that fluctuation is the volatility. This volatility is useful
in systematic trading usually for position sizing.

Eight models make the forecast each day. The repo publishes the one
from whichever model is scoring best so far, in plain language, in
[results/FORECAST.md](results/FORECAST.md). That file gives the
expected move in dollars and percent, where the day sits against the
past year, and which hours are expected to fluctuate most. The
simplest of the eight is
persistence, the naive baseline whose forecast is that each of the next
24 hours will look like the last hour observed. At the other end is
N-HiTS, a neural network built for time series. They run side by side
so the record shows which model families suit this series and which
fail to beat the baseline.

What they forecast is realized volatility, the fluctuation actually
measured from the price, one value per hour. It is measured from
minute-to-minute price changes because an hourly figure needs data
finer than the hour, and one-minute candles are what the exchange
serves. The forecast is hourly because volatility follows a daily
cycle. It runs 24 hours ahead so that one forecast covers a full day.

Every forecast is a quantile band rather than a single number, because
a single number hides how sure the model is. The band has five levels,
the values the truth should fall below 5%, 25%, 50%, 75%, and 95% of
the time. The middle level is therefore the median, and the outer pair
should contain the truth nine times in ten. Whether it does is scored,
which is what makes the band checkable.

Each day, a scheduled run commits every model's forecast to git before
the first of its 24 target hours has ended, so the history proves each
forecast was made before its outcome was known. Each daily
run audits those commit times against the git history and lists the
exceptions in [results/LIVE.md](results/LIVE.md). That file is the
daily record, which holds the running scores of every forecast made
since 2026-08-03.

Scoring is rolling-origin validation. Each forecast is made from one
point in time, its origin, using only data before it, and the origin
steps forward for the next forecast. Every score is therefore out of
sample in time, the same position a live forecast is in.

The band is scored two ways, pinball loss and calibration, because a model can be
accurate with a band too narrow, or well-banded and inaccurate.
Pinball loss scores accuracy. It measures each of the five levels by its
distance from the truth and is lowest on average only when each level
sits at its true value, so a model cannot improve it by hedging wide or
narrow. Calibration scores whether the band's are sized correctly. It counts
how often the truth landed inside the band, against the nine times in
ten the outer pair claims.

Two baselines sit in the results tables beside the other six models.
One is persistence. The other is a HAR model (heterogeneous autoregressive). 
It is a least-squares regression model on the trailing day, week, and month averages
of volatility. It is the published standard baseline for realized
volatility. The skill column measures every model against persistence,
and the table shows which models fail to beat it.

The daily record scores each day's average volatility, the mean of a
model's 24 hourly median forecasts against the mean of the 24 hourly
values that occurred. The error is measured on the log scale, which makes it a
ratio between forecast and truth, so a forecast 20% off counts the same
on a quiet day as on a spike day. A day is fully resolved once all 24
of its hours have been observed. Over the 46 fully resolved days as of
2026-09-22, N-HiTS, the leading model, had an average error of 0.19 on
that scale. Persistence's average error was 0.31 over its 49 days. Lower
is better. Persistence has three more days because N-HiTS joined the daily run
three days after the others. On the 46 days that both models forecast, N-HiTS's
error was 41% below persistence's. That is a day-level skill of 0.41,
where skill is one minus the model's error over persistence's. A zero would 
mean a model ties persistence and a value of one would be a perfect forecast. 
The 95% interval on that skill is 0.18 to 0.64. That interval is the range the true
skill could plausibly sit in given the day-to-day noise, computed as if
each day were independent of the last. It stays above zero, indicating that on those
days the lead over persistence is larger than day-to-day noise would
explain. Those columns and the day-by-day figure are recorded in
[results/LIVE.md](results/LIVE.md), and the figure shows the pattern of
the record. The forecast tracks the level of ordinary days and misses
the spikes on the day they arrive.

The daily record is the live test. The backtest is a one-time run over
the 365 days of history before 2026-08-05. It is kept as the reference
(pinned) rather than re-run. It used a forecast origin
every second day, 183 origins in all. Its best model, N-HiTS, scored a
mean pinball loss of 0.0959 on the log scale, averaged over forecast
horizons of 1 to 24 hours ahead. The persistence baseline scored 0.1180
on the same origins. The skill score, averaged over the same horizons,
is 0.186. A skill of 0.186 means N-HiTS's loss was 18.6% below persistence's.
That backtest's results table, figures, and dataset summary are in
[results/REPORT.md](results/REPORT.md) (generated, never hand-edited).

## Why

The forecast is the product, and the scoring is what makes it worth
reading. Persistence is the bar. A forecast that cannot beat it out of
sample tells you nothing you did not already know, so every forecast
here is committed to the repo's history and scored against persistence
every day.

## Data

The data comes from the exchanges' public data feeds, which need no
account or key. The primary source is Coinbase Exchange 1-minute
candles (one open, high, low, and close per minute), three years of
them for the backtest and one more day of them each morning. Bitstamp hourly closes cross-check them, so the
data is not trusted on one venue's word. On 2026-08-03 that check
compared 26,363 hours and found a median divergence of 0.009%, recorded
in results/crosscheck.txt. The hourly realized volatility built from
those minute-to-minute price changes (1-minute log returns) is
annualized, so its values sit on the per-year scale volatility is
usually quoted in. A value of 0.60 means 60% a year, the fluctuation
to expect over a year if every hour fluctuated like this one. An hour
missing more than a quarter of its minutes is marked missing (NaN)
rather than treated as quiet. The hourly series is committed, in
data/hourly_rv.csv, and grows by 24 rows a day. Each daily run fetches
only the minutes since the series' last hour, builds the new hours from
them, and stores no minutes. The backfill script rebuilds the full
minute history from Coinbase for the backtest, resuming from its last
saved candle.

## Models

| model | family |
|---|---|
| persistence, seasonal persistence | naive baselines, repeating the last hour or the same hour one day earlier |
| HAR (plain and hour-of-day seasonal) | regression on the trailing day, week, and month averages (Corsi-style) |
| SARIMAX (1,0,1)(1,0,1,24) | classical autoregressive time-series model with a 24-hour seasonal cycle |
| Prophet | trend plus daily and weekly cycles (Fourier seasonality) |
| XGBoost | gradient-boosted trees, fit directly to each quantile level |
| N-HiTS | neural network for time series (pytorch-forecasting), fit directly to the quantile loss |

The results tables and the forecast log, results/forecasts.csv, use
short code names for these models: `gbm` is XGBoost, `sarima` is SARIMAX, `har` and
`har_seasonal` are the two HAR variants, and `nhits` is N-HiTS.
`persistence`, `seasonal_persistence`, and `prophet` keep their own
names.

Which model leads is a property of this series. On other data, other
models might dominate, which is why eight run side by side rather than
one being chosen in advance.

## Setup and run

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# The first three commands rebuild the data from scratch for the
# backtest. The daily run does not need them; it starts from the
# committed hourly series.
python scripts/run_backfill.py     # fetch 1-min candles (resumable)
python scripts/run_crosscheck.py   # verify against Bitstamp
python scripts/run_build_rv.py     # build the hourly realized-vol series
python scripts/run_vol_backtest.py # rolling-origin backtest; scores it,
                                   #   logs to MLflow, writes REPORT.md
python scripts/run_vol_report.py   # re-score an existing backtest parquet
                                   #   without refitting
python scripts/run_daily.py        # the daily run: score yesterday, log
                                   #   today's forecasts, write REVIEW.md
                                   #   (yesterday's forecasts against what
                                   #   happened, and the plain-language
                                   #   forecast's own claims scored over
                                   #   every resolved day), LIVE.md (the
                                   #   daily record, with the timing
                                   #   audit's exceptions), and FORECAST.md
                                   #   (the leading model's forecast in
                                   #   plain language), commit and push
                                   #   (--no-push, --no-commit)
python scripts/run_verify_timing.py  # audit the forecast log's timing claim
                                     #   against git history: exits 1 if any
                                     #   forecast row was first committed
                                     #   after its target hour completed
```

`run_vol_backtest.py` takes `--models` (default: every registered model),
`--stride` (default 2, days between forecast origins), and `--test-days`
(default 365) to run subsets quickly, and `--no-report` to stop after
writing the backtest parquet. `run_vol_report.py` takes `--results`
(default: the newest backtest parquet in results/backtest/). `run_daily.py` takes `--no-push`
(commit the run's files locally and do not push) and `--no-commit`
(write every file and commit nothing). Every volatility
backtest run is also logged to MLflow, a local run-tracking tool
(sqlite backend).
Run `mlflow ui --backend-store-uri sqlite:///mlflow.db` to browse the
runs.

On Windows, Prophet's pip wheel worked as-is here (cmdstanpy backend,
no manual install). If a first fit fails with a cmdstan error, run
`python -m cmdstanpy.install_cmdstan` once and retry.

The results folder keeps at its top level the files a reader needs,
with the rest in two subfolders:

- `REPORT.md`, `LIVE.md`, `REVIEW.md`, and `FORECAST.md` are the four
  generated reports described above.
- `forecasts.csv` and `evaluation.csv` are the forecast log and the log
  of every scored forecast, appended by each daily run. The forecast
  log stays at this path because the timing audit reads its git history
  by path.
- `crosscheck.txt` is the output of the Bitstamp cross-check.
- `backtest/` holds each backtest run's scored rows (parquet, not
  committed) with a json file of the same name recording the run's
  settings and the dataset it saw.
- `figures/` holds the three figures the reports embed.

## How the daily run happens

The run is a GitHub Actions workflow,
[.github/workflows/daily-run.yml](.github/workflows/daily-run.yml). A
scheduled task on my machine starts it at 11:15 UTC each day by asking
GitHub to run the workflow, and GitHub's own schedule at 11:15 and
11:45 UTC is the fallback. Whichever fires second does nothing, because
the day's run has already committed. The workflow installs the Python
packages, with the CPU-only build of PyTorch, and runs
`scripts/run_daily.py`, which commits the result as
`github-actions[bot]` and pushes, so the commit times in the forecast
log are GitHub's, not mine. The origin is the 10:00 UTC hour every day,
whatever minute the run starts, so a run that starts late forecasts the
window an on-time run would have and sees no data past that hour. That
hour closes at 11:00, and its first target hour ends at 12:00 UTC, so a
run that starts on time and takes its usual three and a half minutes
commits with about forty minutes to spare. A run that commits after
that is listed in [results/LIVE.md](results/LIVE.md) by the audit, with
what started it and when, read from its commit message. A run that
fails leaves no commit that day, and the gap is visible in the history.

My machine starts the run alongside GitHub's schedule because GitHub's
documentation says a scheduled run can be delayed under load, and the
first scheduled run, on 2026-09-27, started at 15:38 UTC, 4 hours 26
minutes after that day's 11:12 schedule. A run started on request
begins within about a minute. That first run forecast from the 14:00
hour, one of five days in the record off the 10:00 origin. The other
four, 2026-08-03, 08-04, 09-09, and 09-16, were late starts on my
machine. The origin was fixed to the clock the same day. Until
2026-09-26 the run was triggered on my machine alone, at 06:30 local
time and then 06:05 in its last week. The missed day on 2026-09-02 and
the late commit on 2026-09-03 came from an unplanned restart of that
machine. With GitHub's schedule as the fallback, a restart now delays
the run rather than losing it.

The same task then pulls the repo, checks that the day's commit has
landed, and briefs me from
[results/REVIEW.md](results/REVIEW.md),
[results/FORECAST.md](results/FORECAST.md), and
[results/LIVE.md](results/LIVE.md), under rules that it relays
the files' numbers and adds no diagnosis of its own. Its prompt is
committed as [docs/daily_briefing_prompt.md](docs/daily_briefing_prompt.md),
and any scheduled agent or a person can run it.

To run the loop yourself on a clone, fork the repo and enable the
workflow, or schedule `python scripts/run_daily.py --no-push` with
cron or Task Scheduler. The flag keeps the commit on your clone. The
first run needs `data/hourly_rv.csv`, which the repo carries, and
fetches only the minutes since its last hour.

## Tests

```
python -m pytest tests -q
```

The suite checks the realized-volatility formula on a hand-built hour,
proves features are strictly trailing (rewriting the future changes
nothing in the past), enforces the adapter contract for every
registered model, checks pinball loss against hand-computed values, and
proves the backtest engine never hands a model data past its forecast
origin. It also covers the calibration check described in the next
section: that a rejection streak shorter than three days is reported as
pending rather than flagged, that the correction for testing several
models at once scales with their number, and that a model whose daily
coverage has no spread gets no result at all.

## The calibration check

`LIVE.md` carries a `cov90` column, the fraction of hours where the
realized value landed inside a model's 90% band. A calibrated model
sits near 0.90, and a model that sits well below it is claiming more
precision than it has.

The first version of the check compared that column against a fixed
floor of 0.80 and named anything underneath. The check also had a 0.98
ceiling, which no model came near while it was active. From
2026-08-16 to 2026-08-24 the check named `gbm` every day, and from 2026-08-20 on the list
grew to three to five of the eight models. The list never emptied, so
the check carried no information. A signal that is always on cannot
tell you when something changed.

The problem was that the floor sat inside the noise. Hours within a
day move together, so 24 hourly rows carry about one day's worth of
independent evidence, and the sample that matters is the number of
scored days, not the row count. At 21 scored days, a typical model's
day-level coverage has a standard error of about 0.045, the noise
expected in that average from 21 days alone. The gap between the 0.80
floor and the 0.90 target is roughly two standard errors wide. For a
model whose true coverage sits anywhere in the 0.80s, which side of the
floor its estimate lands on is decided by noise. The membership of the
flagged list showed exactly that. On 2026-08-24, `seasonal_persistence`
left the list at 0.8056 while `har_seasonal` stayed on it at 0.7956.
Those two numbers are 0.01 apart, against a standard error of 0.045. The t
statistic counts a model's shortfall below 0.90 in standard errors, so
more negative is stronger evidence. Of the two, `seasonal_persistence`
had the stronger evidence of coverage below target (t = -2.15 against
-1.89), because its day-to-day spread was tighter.
`har` appeared for two days and left. `seasonal_persistence` appeared
for four days and left. Nothing about those models had changed.

Since 2026-08-24 the check tests the evidence instead of the bare
average. It takes each model's coverage one day at a time and runs a
two-sided t-test of those daily figures against 0.90, asking whether
their average sits farther from 0.90, in either direction, than their
own spread explains. A test rejects when it does, and the level is the
false-alarm rate accepted per test, 5%. The check divides that 5% by
the number of models tested (a Bonferroni correction), because eight
tests at 5% each would raise a false alarm often. A model is reported
only after it rejects on three consecutive scored days, so a single
noisy day cannot raise an alarm and a real departure still surfaces
within days. Earlier results are recomputed from `evaluation.csv`, the
log of every scored forecast, rather than stored, so the whole check is
reproducible from that log with no state file that could drift out of
step with the data.

Replayed over every scored day, the check stayed silent through
2026-08-30, and not by a wide margin. `gbm` rejected on 2026-08-26 and
2026-08-27, `prophet` on 2026-08-27 and 2026-08-28, and each streak
broke one day short of the report line. A fresh `gbm` streak began on
2026-08-29. On 2026-08-31 the check reported a model for the first time.
It named `gbm`, whose coverage over its 28 scored days was 0.7932. The
p-value is the chance of a gap that large, in either direction, arising
from noise alone. For `gbm` it was 0.0058, under the corrected
threshold of 0.0063, which is 5% divided by the eight models tested.
`gbm` was the model
nearest the line when the check was rebuilt, so the first flag landing
on it reads as the check doing what it was rebuilt to do. Its bands
stay as the model produces them, and the flag is the published record
that they are too narrow.

The check stays silent in two cases on purpose. A model with fewer than
10 scored days gets no result, because three clean quiet days once
produced a coverage of 1.0 from models the year-long backtest shows are
calibrated. A model whose daily coverage has no spread at all also gets
none, because the test would have no uncertainty to divide by, and
inventing one would repeat the mistake the fixed floor made.

Part of why some bands run narrow is visible in how they are built.
HAR takes its band from the spread of the errors of the regression it
has just fit, on the hours it was fit to. XGBoost fits each of its five
levels to every row of its training window with nothing held back. A
band fitted to the hours a model has seen tends to understate the
errors it makes on hours it has not. In LIVE.md's cov90 column both
models' 90% bands cover fewer than 90% of hours, and so does Prophet's.
The bands are left as each model produces them, because widening them
by hand would hide what the coverage column exists to show.

## Limitations and next steps

The daily record is 49 scored days as of 2026-09-22, and the LIVE.md
results table will stay noisy until the sample grows.

The timing evidence for the forecast log is the commit history. From
2026-09-27 the commits are scheduled to be made by GitHub's runner on
GitHub's clock. Before that they were made by a machine I control, with
the GitHub push history as the independent record for those days. The daily run missed
2026-09-02 entirely after an unplanned restart, and the 2026-09-03
forecast was committed late, which LIVE.md lists. GitHub's scheduler
can start a run hours late, which is why the run is also started from
my machine. A day on which both start late is listed by the audit.

The coverage columns in LIVE.md carry real uncertainty, because each day
contributes about 24 dependent hourly rows. The calibration check above
quantifies that uncertainty rather than reading the column as exact. It
treats each scored day as independent of the last, and that day-to-day
dependence is unmodeled. If consecutive days move together, the check
and the interval above are more confident than they should be. As of 2026-09-22, five of the eight
models' coverage sits below 0.90 and the other three sit just above it.
That mostly one-sided pattern is a weak signal that the bands are
narrow, and no per-model test will settle it at this sample size. A
pattern like that is why the check was rebuilt rather than removed.

The 2026-08-19 forecast day shows the pattern of the whole record.
Realized volatility ran 3.67 times the nhits median forecast, and on
2026-08-21 the fixed-floor calibration check flagged five models below
its 0.80 coverage floor, its widest list. The forecast tracks the level
of ordinary days, and the rare day that breaks the
pattern is not signaled by the hours before it.

The backtest covers one asset, BTC-USD, a market that trades every
hour of every day. Nothing here shows the ranking holds on other
markets, and a market with a daily close would need the volatility
rule, the persistence baseline, and the 24-hour horizon rethought
around its session. The backtest and the daily record are also two different
experiments. The backtest's origins sit at midnight UTC, while the
daily run's origin is the 10:00 UTC hour, so the backtest ranking has
not been measured at the hour the daily run forecasts from.
