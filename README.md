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
simplest of the eight is persistence, the naive baseline whose forecast
is that each of the next 24 hours will look like the last hour observed.
The most complex is N-HiTS, a neural network built for time series.
They run side by side so the record shows which model families suit
this series and which fail to beat the baseline.

## The result so far

The daily record, [results/LIVE.md](results/LIVE.md), holds the running
scores of every forecast made since 2026-08-03. On the 56 days that both
N-HiTS and persistence forecast, as of 2026-10-02, N-HiTS's error on
each day's average volatility was 39% below persistence's.

![day by day: forecast, realized, persistence](results/figures/fig_live_daily.png)

The figure is that record day by day for the leading model: its
forecast of each day's average volatility, the average that occurred,
and the persistence model's own forecast of the same average. Every
daily run redraws it, so it extends past the dated numbers in this
section. The forecast tracks the level of ordinary days and misses the
spikes on the day they arrive.

The daily record scores each day's average volatility, the mean of a
model's 24 hourly median forecasts against the mean of the 24 hourly
values that occurred. The median forecast is the middle of the band of
values a model gives for each hour. The error is the log of realized
over forecast value, sign ignored, so a forecast 20% off counts the
same on a quiet day as on a spike day. A day is fully resolved once all 24
of its hours have been observed. Over the 56 fully resolved days as of
2026-10-02, N-HiTS, the leading model, had an average error of 0.18 on
that scale. Persistence's average error was 0.29 over its 59 days.
Lower is better. Persistence has three more days because N-HiTS joined
the daily run three days after the others. The 39% above is measured
on the 56 days that both models forecast, and its 95% interval runs
from 18% to 60%. That interval is the range the true lead could
plausibly sit in given the day-to-day noise, computed as if each day
were independent of the last. It stays above zero, indicating that on
those days the lead over persistence is larger than day-to-day noise
would explain. The error is a column in LIVE.md's table, and the
interval is stated under it.

## What is forecast

What the models forecast is realized volatility, the fluctuation actually
measured from the price, one value per hour. It is measured from
minute-to-minute price changes because an hourly figure needs data
finer than the hour, and one-minute candles are what the exchange
serves. The forecast is hourly because volatility follows a daily
cycle. It runs 24 hours ahead so that one forecast covers a full day.

Every forecast is a quantile band rather than a single number. A single
number hides how sure the model is but quantiles naturally represent
model confidence. The band is five values for each hour, the 5%, 25%,
50%, 75%, and 95% quantiles, with the 50% quantile representing the
median. Each quantile is named for the probability that the realized
volatility does not exceed it. The realized volatility should therefore
sit between the highest and lowest quantiles 90% of the time.
The scoring counts how often the realized volatility lands within
those bounds.

## How it is scored

Each day, a scheduled run commits every model's forecast to git before
the first of its 24 target hours has ended, so the history proves each
forecast was made before its outcome was known. Each daily run audits
those commit times against the git history and lists the days whose
commit came late in the daily record. Those days stay in the scores,
and the list records them.

Scoring is rolling-origin validation. Each forecast is made from one
point in time, its origin, using only data before it, and the origin
steps forward for the next forecast. Every score is therefore out of
sample in time, the same position a live forecast is in.

The band is scored two ways, pinball loss and calibration, because a
model can be accurate with a band too narrow, or well-banded and
inaccurate. Pinball loss scores accuracy. It measures each of the five
quantiles by its distance from the realized value. It is lowest on
average only when each quantile sits at its true value, so a model
cannot improve it by hedging wide or narrow. Calibration scores whether
the bands are sized correctly. It counts how often the realized value
landed inside the 90% band, the span between the 5% and 95% quantiles.

Two baselines sit in the results tables beside the other six models.
One is persistence. The other is HAR (heterogeneous autoregressive),
the published standard baseline for realized volatility; both are
described under Models. The skill column measures every model against
persistence. Skill is one minus the model's error over persistence's,
so zero ties persistence, one would be a perfect forecast, and a
negative value loses to the baseline. The table shows which models do.

## Why

The forecast is the product, and the scoring is what makes it worth
reading. Persistence is the bar. A forecast that cannot beat it out of
sample tells you nothing you did not already know, so every forecast
here is committed to the repo's history and scored against persistence
every day.

## Data

The data comes from the exchanges' public data feeds, which need no
account or key. The primary source is Coinbase Exchange 1-minute candles
(one open, high, low, and close per minute), three years of them for the
backtest and one more day of them each morning. Bitstamp hourly closes
cross-check them, so the data is not trusted on one venue's word. On
2026-08-03 that check compared 26,363 hours and found a median
divergence of 0.009%, recorded in results/crosscheck.txt. The hourly
realized volatility built from those minute-to-minute price changes
(1-minute log returns) is annualized, so its values sit on the per-year
scale volatility is usually quoted in. A value of 0.60 means 60% a year,
the fluctuation to expect over a year if every hour fluctuated like this
one. An hour missing more than a quarter of its minutes is marked
missing (NaN) rather than treated as quiet. The hourly series is
committed, in data/hourly_rv.csv, and grows by 24 rows a day. Each daily
run fetches only the minutes since the series' last hour, builds the new
hours from them, and stores no minutes. The backfill script rebuilds the
full minute history from Coinbase for the backtest, resuming from its
last saved candle.

## Models

Eight models run side by side. Each is listed under the name it carries
in the results tables and the forecast log, with the family it belongs
to and where its band comes from.

- `persistence`. The naive baseline. Its forecast for each of the next
  24 hours is the last hour observed. Its band comes from how much the
  series moved over each horizon in the training window.
- `seasonal_persistence`. The seasonal naive baseline. Its forecast for
  each hour is the value at the same hour one day earlier, with one
  band width for every horizon, taken from day-over-day changes.
- `har` (heterogeneous autoregressive). The published standard baseline
  for realized volatility. A least-squares regression of each future
  hour on the last hour and the trailing day, week, and month averages,
  one regression per horizon. Its band comes from the spread of that
  regression's own errors.
- `har_seasonal`. HAR with the hour of day added as a regressor, so the
  forecast can shift with the daily cycle. Its band is built the same
  way as HAR's.
- `sarima` (SARIMAX). A classical time-series model fit on the most
  recent 90 days. Its order, (1,0,1)(1,0,1,24), means one term carrying
  over from the previous hour and one from the previous hour's error,
  with the same pair at a lag of 24 hours for the daily cycle. The
  zeros mean no differencing, because log volatility stays roughly
  level over time.
  The X stands for outside inputs, and none are used. Its band is
  symmetric, from the forecast's standard error.
- `prophet` (Prophet). A trend-plus-cycles model with daily and weekly
  cycles and no yearly one. Its band comes from 300 simulated draws of
  its own forecast.
- `gbm` (XGBoost). Gradient-boosted trees, one model per quantile
  level, trained to the pinball loss on lagged values, the trailing
  averages, the hour of day and day of week, and the forecast horizon
  as an input.
- `nhits` (N-HiTS). A neural network built for time series, trained
  from scratch each day with one week of context and all five quantile
  levels at once, for three passes over the training window. It is
  kept small on purpose, so it runs on a CPU inside the daily run.

Every model but SARIMAX trains on the past 365 days. Each model's
settings were fixed in the commit that created it and have not been
changed since.

Which model leads is a property of this series. On other data, other
models might dominate, which is why eight run side by side rather than
one being chosen in advance.

The daily record is the live test. The backtest is a one-time run over
the 365 days of history before 2026-08-05, kept as the reference
(pinned) rather than re-run. It used a forecast origin every second
day, 183 origins in all. Its winner, N-HiTS, is the model whose
forecast the daily run published until the live scores could choose
one. N-HiTS scored a mean pinball loss of 0.0959 on the log scale,
averaged over forecast horizons of 1 to 24 hours ahead, against 0.1180
for persistence on the same origins. That is a skill of 0.186, meaning
its loss was 18.6% below persistence's. That backtest's results table,
figures, and dataset summary are in
[results/REPORT.md](results/REPORT.md) (generated, never hand-edited).

## Setup and run

Requires git and Python 3.11 or later. No GPU is needed.

In a terminal, run the following commands.

1. Clone the repository:

   ```
   git clone https://github.com/RAStevenson/bitcoin-volatility-forecast.git
   ```

2. Navigate to the root directory:

   ```
   cd bitcoin-volatility-forecast
   ```

3. Create a new environment and activate it (on Mac or Linux the second
   line is `source .venv/bin/activate`):

   ```
   python -m venv .venv
   .venv\Scripts\activate
   ```

4. Install PyTorch from its CPU-only index, then the rest of the
   dependencies:

   ```
   pip install torch==2.13.0 --index-url https://download.pytorch.org/whl/cpu
   pip install -r requirements.txt
   ```

   PyTorch installs without a GPU either way. The first line matters on
   Linux, where the default PyTorch package also downloads large CUDA
   libraries that these models never use. On Windows
   the default package is already CPU-only. The pinned versions in
   `requirements.txt` are the ones the daily run installs.

The scripts, in the order a rebuild from scratch would run them:

```
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

`run_vol_backtest.py` takes `--models` (default: every registered
model), `--stride` (default 2, days between forecast origins), and
`--test-days` (default 365) to run subsets quickly, and `--no-report` to
stop after writing the backtest parquet. `run_vol_report.py` takes
`--results` (default: the newest backtest parquet in results/backtest/).
`run_daily.py` takes `--no-push` (commit the run's files locally and do
not push) and `--no-commit` (write every file and commit nothing). Every
volatility backtest run that writes its report is also logged to MLflow,
a local run-tracking tool (sqlite backend). Run `mlflow ui
--backend-store-uri sqlite:///mlflow.db` to browse the runs.

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
GitHub to run the workflow, and GitHub's own schedule at 11:15 and 11:45
UTC is the fallback. Whichever fires second does nothing, because the
day's run has already committed. The workflow installs the Python
packages, with the CPU-only build of PyTorch, and runs
`scripts/run_daily.py`, which commits the result as
`github-actions[bot]` and pushes, so the commit times in the forecast
log are GitHub's, not mine. The origin is the 10:00 UTC hour every day,
whatever minute the run starts, so a run that starts late forecasts the
window an on-time run would have, and its models see no data past that
hour. Only the dollar figures in FORECAST.md use the price at the time
of the run. The 10:00 hour is 5:00 in the morning in Chicago, 4:00 once
daylight saving ends, so the forecast and its briefing land before the
US stock market opens at 8:30 Central, and the 24 hours it covers
include that session. The origin hour closes at 11:00, and its first
target hour ends at 12:00 UTC, so a run that starts on time and takes
its usual three and a half minutes commits with about forty minutes to
spare. A run that commits after that is listed in
[results/LIVE.md](results/LIVE.md) by the audit, with what started it
and when, read from its commit message. A run that fails leaves no
commit that day, and the gap is visible in the history.

My machine starts the run because GitHub's documentation says a
scheduled run can be delayed under load, and the first scheduled run of
this workflow started 4 hours 26 minutes late. A run started on request
begins within about a minute. The origin has been fixed at 10:00 since
2026-09-27, the day of that late run. The five earlier days whose
origin was not 10:00 are visible in the forecast log. Before the move
to GitHub the run was triggered on my machine alone, and one unplanned
restart of it cost a missed day, 2026-09-02, which is a gap in the
history, and a late commit, which the audit lists.

The same task then pulls the repo, checks that the day's commit has
landed, and briefs me from
[results/REVIEW.md](results/REVIEW.md),
[results/FORECAST.md](results/FORECAST.md), and
[results/LIVE.md](results/LIVE.md), under rules that it relays
the files' numbers and adds no diagnosis of its own. Its prompt is
committed as [docs/daily_briefing_prompt.md](docs/daily_briefing_prompt.md),
and any scheduled agent or a person can run it. The prompt says which
steps a reader without write access runs.

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
checks that features are strictly trailing (rewriting the future changes
nothing in the past), checks the fit-and-predict contract every
registered model implements, checks pinball loss against hand-computed
values, and confirms that the backtest engine never hands a model data
past its forecast origin. It also covers the calibration check described
in the next section: that a rejection streak shorter than three days is
reported as pending rather than flagged, that the correction for testing
several models at once scales with their number, and that a model whose
daily coverage has no spread gets no result at all.

## The calibration check

`LIVE.md` carries a `cov90` column, the fraction of hours where the
realized value landed inside a model's 90% band. A calibrated model
sits near 0.90, and a model that sits well below it is claiming more
precision than it has.

Each daily run checks whether a model's coverage is farther from 0.90,
in either direction, than noise would explain, taking each model's
coverage one day at a time, with a correction for testing eight models
at once. A model is flagged only after it sits farther from 0.90 than
noise explains on three consecutive scored days, and a shorter streak
is reported as pending. Each day's LIVE.md states the test in full. Earlier results are
recomputed from `evaluation.csv`, the log of every scored forecast,
rather than stored, so the whole check is reproducible from that log.

The check stays silent in two cases on purpose. A model with fewer than
10 scored days gets no result, because three clean quiet days once
produced a coverage of 1.0 from models the year-long backtest shows are
calibrated. A model whose daily coverage has no spread at all also gets
none, because the test would have no uncertainty to divide by, and
inventing one would be a guess.

Part of why some bands run narrow is visible in how they are built.
HAR takes its band from the spread of the errors of the regression it
has just fit, on the hours it was fit to. XGBoost fits each of its five
quantiles to every row of its training window with nothing held back. A
band fitted to the hours a model has seen tends to understate the
errors it makes on hours it has not. In LIVE.md's cov90 column both
models' 90% bands cover fewer than 90% of hours, and so does Prophet's.
The bands are left as each model produces them, because widening them
by hand would hide what the coverage column exists to show.

The check replaced an earlier version that named any model under 0.80
coverage. How that version failed and which models the current one has
flagged are recorded in
[docs/calibration_check_history.md](docs/calibration_check_history.md).

## Limitations and next steps

The daily record is 59 scored days as of 2026-10-02, and the LIVE.md
results table will stay noisy until the sample grows.

The timing evidence for the forecast log is the commit history. Since
2026-09-27 the commits are made by GitHub's runner on GitHub's clock.
Before that they were made by a machine I control, and the audit reads
commit times only, so those days depend on that machine's clock. The
audit in LIVE.md lists every exception.

The coverage columns in LIVE.md carry real uncertainty, because each day
contributes about 24 dependent hourly rows. The calibration check above
quantifies that uncertainty rather than reading the column as exact. It
treats each scored day as independent of the last, and that day-to-day
dependence is unmodeled. If consecutive days move together, the check
and the interval above are more confident than they should be. As of
2026-10-02, six of the eight models' coverage sits below 0.90 and the
other two sit just above it. That mostly one-sided pattern is a weak
signal that the bands are narrow, and no per-model test will settle it
at this sample size.

The 2026-08-19 forecast day shows the pattern of the whole record.
Realized volatility ran 3.67 times the nhits median forecast. The
forecast tracks the level of ordinary days, and the rare day that
breaks the pattern is not signaled by the hours before it.

The backtest covers one asset, BTC-USD, a market that trades every
hour of every day. Nothing here shows the ranking holds on other
markets, and a market with a daily close would need the volatility
rule, the persistence baseline, and the 24-hour horizon rethought
around its session. The backtest and the daily record are also two different
experiments. The backtest's origins sit at midnight UTC, while the
daily run's origin is the 10:00 UTC hour, so the backtest ranking has
not been measured at the hour the daily run forecasts from.
