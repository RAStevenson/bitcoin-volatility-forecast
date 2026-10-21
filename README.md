# bitcoin-volatility-forecast

This repo publishes a daily forecast of how much the price of BTC-USD
(Bitcoin priced in US dollars) will fluctuate over the next 24 hours,
and holds the code that scores that forecast against reality. The size
of that fluctuation is called the volatility. This volatility is useful
in systematic trading, usually for position sizing.

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
over forecast value, sign ignored, so a forecast 20% off counts the same
on a quiet day as on a spike day. A day is fully resolved once all 24 of
its hours have been observed. Over the 56 fully resolved days as of
2026-10-02, N-HiTS, the leading model, had an average error of 0.18 on
that scale. Persistence's average error was 0.29 over its 59 days. Lower
is better. Persistence has three more days because N-HiTS joined the
daily run three days after the others. The 39% above is measured on the
56 days that both models forecast, and its 95% interval runs from 18% to
60%. That interval is the range the true lead could plausibly sit in
given the day-to-day noise, computed as if each day were independent of
the last. It stays above zero, indicating that on those days the lead
over persistence is larger than day-to-day noise would explain. The
error is the day_error column in LIVE.md's table, each model over its
own days, and the matched comparison is the day_skill column, with the
interval stated under the table.

## Getting the daily forecast

The day's forecast can be read on GitHub with no clone of the repo and
none of its Python packages. Each day's run rewrites three reports,
usually by 11:20 UTC. [FORECAST.md][forecast] holds the day's
forecast, [REVIEW.md][review] says how yesterday's forecast did, and
[LIVE.md][live] is the daily record of every model's scores.

An AI agent can also fetch the three reports and summarize them
each day. The instructions it follows are the briefing prompt,
[daily_briefing_prompt.md][prompt]. It can be scheduled after 12:00
UTC in Claude Code or any other agent that can run shell commands.
Each run writes a short briefing that leads with the forecast, or
says the forecast has not landed yet on a day the daily run is
late. Run this way, the prompt reads the three reports and runs
nothing.

## What is forecast

What the models forecast is realized volatility, the fluctuation actually
measured from the price, one value per hour. It is measured from
minute-to-minute price changes because an hourly figure needs data
finer than the hour, and one-minute candles are what the exchange
serves. The forecast is hourly because volatility follows a daily
cycle. It runs 24 hours ahead so that one forecast covers a full day.

Every forecast is a quantile band rather than a single number. A point
estimate is just a single number with no additional information, but
quantiles are more valuable because they naturally represent model
confidence. The width of the band is the model's own statement of
uncertainty. It is wide when the forecast is unsure and narrow when its
confidence is higher. The band is five values for each hour, the 5%,
25%, 50%, 75%, and 95% quantiles, with the 50% quantile representing the
median. Each quantile is named for the probability that the realized
volatility does not exceed it. The realized volatility should therefore
sit between the highest and lowest quantiles 90% of the time. The
scoring counts how often the realized volatility lands within those
bounds.

## How it is scored

Each day, a scheduled run commits every model's forecast to git before
the first of its 24 target hours has ended, so the history proves each
forecast was made before its outcome was known. Each daily run audits
those commit times against the git history and lists the days whose
commit came late in the daily record. Those days stay in the scores,
and the list records them.

Each forecast is made from one point in time, its origin, using only
data before it, and the origin steps forward for the next forecast. This
is rolling-origin evaluation. Every score is therefore out of sample in
time, the same position a live forecast is in.

The band is scored two ways, pinball loss and calibration, because a
model can be accurate with a band too narrow, or well-banded and
inaccurate. Pinball loss scores accuracy. It measures each of the five
quantiles by its distance from the realized value. It is lowest on
average only when each quantile sits at its true value, so a model
cannot improve it by hedging wide or narrow. Calibration scores whether
the bands are sized correctly. It counts how often the realized value
landed inside the 90% band, the span between the 5% and 95% quantiles.
LIVE.md reports that share as the `cov90` column.

Two baselines sit in the results tables beside the other six models. One
is persistence. The other is HAR (heterogeneous autoregressive), the
published standard baseline for realized volatility; both are described
under Models. The skill column measures every model against persistence.
Skill is one minus the model's error over persistence's, so zero ties
persistence, one would be a perfect forecast, and a negative value loses
to the baseline. The table shows the current performance.

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
  24 hours is the single last hour observed with no fluctuation. Its
  band is an empirical prediction interval, built from the forecast's
  past errors. Persistence's error some hours ahead is how much
  volatility changed over those hours. Each forecast hour's band is the
  last observed value plus the spread of those changes over the past
  year. The band widens over the first few hours, then levels off
  because volatility tends to return toward its usual level.
- `seasonal_persistence`. The seasonal naive baseline. Its forecast for
  each hour is the value at the same hour one day earlier, so it repeats
  yesterday's daily pattern. Its band is also an empirical prediction
  interval. Each forecast copies a value from exactly one day earlier,
  so its error is how much volatility changed between an hour and the
  same hour the next day. Each forecast hour's band is yesterday's value
  at that hour plus the spread of those day-over-day changes over the
  past year. The band has the same width on the log scale at every hour,
  because the gap to the copied value is always one day.
- `har` (heterogeneous autoregressive). The published standard baseline
  for realized volatility. It forecasts from four inputs, the last hour
  and the averages over the trailing day, week, and month. Mixing those
  time spans lets it follow both quick swings and slow shifts in the
  level. It is a least-squares regression, fit separately for each of
  the 24 hours ahead. Its band is also an empirical prediction interval.
  Each forecast hour's band is the regression's forecast plus the spread
  of that regression's own errors on the past year, the same year it was
  fit to.
- `har_seasonal`. HAR with one more input, the hour of day the forecast
  starts from. Each of the 24 hours ahead has its own regression, so the
  starting hour tells each one which hour of the day it is forecasting.
  Its forecast can therefore follow the daily cycle, which plain HAR's
  cannot. Its band is built the same way as HAR's.
- `sarima` (SARIMAX - seasonal autoregressive integrated moving
  average). A classical time-series model. It forecasts each hour from
  the hour before and from the same hour a day earlier. It also uses the
  error of its own forecasts for those two hours as a component. The
  seasonal part is a one-day lookback. The X allows outside inputs, and
  none are used here. It is fit on the most recent 90 days. Its band is
  a model-based prediction interval rather than an empirical one,
  assuming a normal (bell-curve) error around each forecast. The band is
  symmetric on the log scale and widens with the hours ahead.
- `prophet` (Prophet). A trend-plus-cycles model released by Facebook
  (now Meta) in 2017. It fits a slowly changing trend plus repeating
  daily and weekly cycles, with no yearly one. It forecasts each hour
  from where the trend and the cycles put it, not from the latest hours.
  Its band is simulation-based. Prophet draws 300 possible futures from
  its fitted model. Each forecast hour's band is the spread of those
  draws at that hour, so the band rises and falls with the daily cycle.
- `gbm` (XGBoost). Gradient-boosted trees, meaning many small decision
  trees added one after another, each correcting the errors of those
  before it. Its inputs are lagged values, the trailing averages, the
  hour of day and day of week, and the number of hours ahead, so no hour
  ahead needs a model of its own. Its band comes from quantile
  regression. Five separate models, one per quantile level, are each
  trained to minimize the pinball loss for their own level. Each
  quantile of the band is therefore predicted directly rather than built
  from past errors.
- `nhits` (N-HiTS). A neural network built for time series. It is made
  of blocks that each read the past week at a different level of detail,
  from slow swings to hour-to-hour changes. Their outputs add up to the
  24-hour forecast. N-HiTS was first published in 2022 as a successor to
  N-BEATS (2019), which uses the same stack of blocks without the
  different levels of detail. N-HiTS's only input is the volatility
  series itself, with no clock input, and it picks up the daily cycle
  from the series. Like XGBoost's, its band comes from quantile
  regression, but one network produces all five quantile levels at once.
  It is retrained from scratch each day for three passes over the
  training window and kept small on purpose, so it runs on a CPU inside
  the daily run.

Every model except SARIMAX trains on the past 365 days. Each model's
settings were selected during initial creation and have not been
changed since. No model has ever been tuned, and a tuning update is
planned.

Which model is the leading model depends on the data. On other data,
other models might dominate, which is why eight run side by side rather
than one being chosen in advance.

The record is the live test committed daily. The backtest is a one-time
run over the 365 days of history before 2026-08-05, kept as the
reference (pinned) rather than re-run. It used a forecast origin every
second day, 183 origins in all. Its winner, N-HiTS, is the model the
daily run falls back to while fewer than three days are scored. N-HiTS
scored a mean pinball loss of 0.0959 on log volatility (lower is
better), averaged over forecast horizons of 1 to 24 hours ahead,
against 0.1180 for persistence on the same origins. The skill score
averaged over the same horizons is 0.186 (higher is better), meaning
its loss was 18.6% below persistence's on an average horizon. That
backtest's results table, figures, and dataset summary are in
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
   libraries that these models never use. On Windows the default package
   is already CPU-only. The pinned versions in `requirements.txt` are
   the ones the daily run installs.

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
                                     #   against git history, listing each
                                     #   late day with its reason; exits 1
                                     #   if a late day has no reason
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

The run is a GitHub Actions workflow, [daily-run.yml][workflow]. A
Windows Task Scheduler entry on the author's machine starts it at
11:15 UTC each day by asking GitHub to run the workflow, and GitHub's
own schedule at 11:15 and 11:45 UTC is the fallback. Whichever fires
second does nothing, because the day's run has already committed. The
workflow installs the Python packages, with the CPU-only build of
PyTorch, and runs `scripts/run_daily.py`, which commits the result as
`github-actions[bot]` and pushes, so the commit times in the forecast
log are GitHub's, not the author's. The origin is the 10:00 UTC hour
every day, whatever minute the run starts, so a run that starts late
forecasts the window an on-time run would have, and its models see no
data past that hour. Only the dollar figures in FORECAST.md use the
price at the time of the run. The 10:00 UTC hour is 5:00 am CDT in
Chicago, or 4:00 am CST once daylight saving ends. The forecast and
its briefing therefore land before the US stock market opens at 8:30
am Central, and the 24 hours it covers include that session. The
origin hour closes at 11:00, and its first target hour ends at 12:00
UTC, so a run that starts on time and takes its usual three and a half
minutes commits with about forty minutes to spare. A run that commits
after that is listed in [LIVE.md][live] by the audit, with what
started it and when, read from its commit message. A run that fails
leaves no commit that day, and the gap is visible in the history.

[workflow]: .github/workflows/daily-run.yml

The author's machine starts the run, with GitHub's own schedule as the
backup, because GitHub's documentation says a scheduled run can be
delayed under load. This was confirmed by experience, as the first
scheduled run launched by GitHub Actions started 4 hours 26 minutes
late. Under the fixed 10:00 UTC origin, a run that late would commit
after the forecast's first target hours had passed and after the US
stock market had opened.

After the run, a Claude Code scheduled task pulls the repo and checks
that the day's commit has landed. If the GitHub run failed or never
started, the task runs `scripts/run_daily.py` on the author's machine
instead. Either way, it then writes a briefing for the author from
[FORECAST.md][forecast], [REVIEW.md][review], and [LIVE.md][live], under
rules that it relays the files' numbers and adds no diagnosis of its
own. Its prompt is committed as [daily_briefing_prompt.md][prompt], and
for the owner of a fork it gives the PowerShell lines that register the
Task Scheduler entry.

[forecast]: results/FORECAST.md
[review]: results/REVIEW.md
[live]: results/LIVE.md
[prompt]: docs/daily_briefing_prompt.md

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
past its forecast origin.

## Limitations

- The daily record is 59 scored days as of 2026-10-02, and the LIVE.md
  results table is noisy but will likely become more stable as samples
  grow.

- The timing evidence for the forecast log is the commit history. Since
  2026-09-27 the commits are made by GitHub's runner on GitHub's clock.
  Before that they were made by the author's machine, and the audit
  reads commit times only, so those days depend on that machine's clock.
  The audit in LIVE.md lists every exception.

- The 95% interval on N-HiTS's lead over persistence, near the top of
  this README, treats each scored day as independent of the last. If
  consecutive days move together, the interval will be narrower than it
  should be.

- The 2026-08-19 forecast day illustrates an important limitation. It
  was an abnormally volatile day, with realized volatility at 3.67 times
  the N-HiTS median forecast. But the forecast tracks the level of
  ordinary days. Rare days that break the pattern are not usually
  signaled by the hours before them.

- The backtest covers one asset, BTC-USD, a market that trades every
  hour of every day. Nothing here shows the ranking holds on other
  markets, and a market with a daily close would need the volatility
  rule, the persistence baseline, and the 24-hour horizon rethought
  around its session. The backtest and the daily record are also two
  different experiments. The backtest's origins sit at midnight UTC,
  while the daily run's origin is the 10:00 UTC hour, so the backtest
  ranking has not been measured at the hour the daily run forecasts
  from.
