# volatility-forecast-harness

This repo publishes a daily forecast of how volatile BTC-USD will be over
the next 24 hours, and holds the harness that scores it against what
happens. A forecast of the coming day's volatility could be one input to
a position size. Model families from naive persistence to a deep net
produce next-24-hour quantile forecasts of hourly realized volatility, a
predicted low/median/high band rather than a single number. Each day the
loop runs, every model's forecast is committed to git before the first of
its 24 target hours has ended. Each daily run audits those commit times
against the git history and lists the exceptions in
[results/LIVE.md](results/LIVE.md). Evaluation is rolling-origin temporal
validation, where the forecast origin steps forward through time and each
forecast sees only data before it, with quantile accuracy (pinball loss)
and calibration (how often the truth lands inside the band) scored
separately. Every model is scored against two baselines,
persistence and the HAR (heterogeneous autoregressive) regression
standard in volatility work, and the results table shows which models fail
to beat them.

Over the 46 fully resolved days to 2026-09-22, the leading
model, N-HiTS, forecast each day's average volatility with a miss of
0.19 in log units, a miss of about a fifth. Persistence missed by 0.31
over its 49 days. On the 46 days both forecast, the day-level skill is
0.41, with a 95% interval of 0.18 to 0.64 that treats each day as
independent of the last. The interval stays above zero, so on those days
the lead over persistence is larger than day-to-day noise would explain.
Those columns and the day-by-day figure are in
[results/LIVE.md](results/LIVE.md), and the figure shows the pattern of
the record. The forecast tracks the level of ordinary days and misses
the spikes on the day they arrive.

In the pinned 2026-08-05 backtest, the best model (N-HiTS, the deep
net) scored a mean pinball loss of 0.0959 against 0.1180 for the
persistence baseline, a skill score of 0.186, meaning it removed about a
fifth of the baseline's error, averaged over forecast horizons of 1 to 24
hours. The backtest covers the last 365 days of the data, with a forecast
origin every second day, 183 origins in all. The current tournament
results, figures, and dataset summary are in
[results/REPORT.md](results/REPORT.md) (generated, never hand-edited).

## Why

The forecast is the product, and the scoring is what makes it worth
reading. Persistence, the baseline that says tomorrow will look like
today, is the bar. A forecast that cannot beat it out of sample tells
you nothing you did not already know, so every forecast here is
committed in public and scored against persistence every day.
The harness is not tied to one series, as long as the series is hourly.
Models implement a small adapter (train window in, quantile forecasts
out), and any hourly series with a timestamp index plugs in; the load
demo below shows it.

## Data

The data comes from public exchange APIs that need no API key. Coinbase
Exchange 1-minute candles (one open, high, low, and close per minute) are
the primary source, three years of them and growing daily. Bitstamp
hourly closes cross-check them. On 2026-08-03 that check compared 26,363
hours and found a median divergence of 0.009%, recorded in
results/crosscheck.txt. Hourly realized
volatility is computed from 1-minute log returns, annualized, with hours
missing more than a quarter of their minutes marked missing (NaN) rather than treated
as quiet. Raw data is not committed. The backfill resumes from its last
saved candle and rebuilds the dataset from the exchanges.

## Models

| model | family |
|---|---|
| persistence, seasonal persistence | naive baselines |
| HAR (plain and hour-of-day seasonal) | econometric baseline (Corsi-style) |
| SARIMAX (1,0,1)(1,0,1,24) | classical time series with a 24-hour seasonal cycle |
| Prophet | Fourier daily/weekly seasonality |
| XGBoost | gradient boosting, native quantile objective |
| N-HiTS | deep learning (pytorch-forecasting), native quantile loss |

The results tables and the forecast log use short code names for these
models: `gbm` is XGBoost, `sarima` is SARIMAX, `har` and
`har_seasonal` are the two HAR variants, and `nhits` is N-HiTS.

A second dataset, German hourly load (OPSD/ENTSO-E, CC-BY 4.0), runs
through the identical engine as a generality demo:
[results/LOAD_REPORT.md](results/LOAD_REPORT.md). The model ranking
reorders against the volatility tournament, with Prophet climbing
from third from last to second, which is the point. Model family choice
depends on series structure, and the harness measures it.

## Setup and run

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

python scripts/run_backfill.py     # fetch 1-min candles (resumable)
python scripts/run_crosscheck.py   # verify against Bitstamp
python scripts/run_build_rv.py     # build the hourly realized-vol series
python scripts/run_vol_backtest.py # rolling-origin tournament; scores it,
                                   #   logs to MLflow, writes REPORT.md
python scripts/run_vol_report.py   # re-score an existing backtest parquet
                                   #   without refitting
python scripts/run_load_demo.py    # generality demo: German hourly load
                                   #   through the same engine, writes
                                   #   LOAD_REPORT.md
python scripts/run_daily.py        # the daily run: score yesterday, log
                                   #   today, write results/REVIEW.md
                                   #   (yesterday's forecast vs realized,
                                   #   and the outlook's own claims scored
                                   #   over every resolved day), LIVE.md
                                   #   (with the timing audit's exceptions)
                                   #   and OUTLOOK.md, commit and push
python scripts/run_verify_timing.py  # audit the forecast log's timing claim
                                     #   against git history: exits 1 if any
                                     #   forecast row was first committed
                                     #   after its target hour completed
```

`run_vol_backtest.py` takes `--models` (default: every registered model),
`--stride` (default 2, days between forecast origins), and `--test-days`
(default 365) to run subsets quickly, and `--no-report` to stop after
writing the backtest parquet. `run_load_demo.py` takes `--stride` (default 4) and `--test-days`
(default 365) with the same meanings. `run_vol_report.py` takes `--results`
(default: the newest backtest parquet in results/). Experiment tracking is local MLflow (sqlite backend). Run
`mlflow ui --backend-store-uri sqlite:///mlflow.db` to browse the runs.

On Windows, Prophet's pip wheel worked as-is here (cmdstanpy backend,
no manual install). If a first fit fails with a cmdstan error, run
`python -m cmdstanpy.install_cmdstan` once and retry.

## Tests

```
python -m pytest tests -q
```

The suite pins the realized-vol closed form, proves features are strictly
trailing (rewriting the future changes nothing in the past), enforces the
adapter contract for every registered model, checks pinball loss against
hand-computed values, and uses a spy model to prove the backtest engine
never shows a model data past its origin. It also pins the calibration
check: that a rejection streak shorter than the three-consecutive-day
requirement is reported as pending rather than flagged, that the multiple-comparison correction
scales with the number of models tested, and that a model whose daily
coverage has no spread gets no result at all.

## The calibration check

`LIVE.md` carries a `cov90` column, the fraction of hours where the
realized value landed inside a model's 90% band. A calibrated model
sits near 0.90, and a model that sits well below it is claiming more
precision than it has.

The first version of the check compared that column against a fixed
floor of 0.80 (the band also had a 0.98 ceiling no model came
near while the check was active) and named anything underneath. From 2026-08-16 to
2026-08-24 it named `gbm` every day, and from 2026-08-20 on the list
grew to three to five of the eight models. The list never emptied, so
the check carried no information. A signal that is always on cannot
tell you when something changed.

The problem was that the floor sat inside the noise. Hourly rows within
a day are strongly dependent, so the effective sample is the number of
scored days, not the row count. At 21 scored days the standard error
of a typical model's day-level coverage, the noise expected in that
average from 21 days alone, is about 0.045. The gap between the 0.80
floor and the 0.90 target is roughly two standard errors wide. For a
model whose true coverage sits anywhere in the 0.80s, which side of the
floor its estimate lands on is decided by noise. The membership of the
flagged list showed exactly that. On 2026-08-24, `seasonal_persistence`
left the list at 0.8056 while `har_seasonal` stayed on it at 0.7956.
Those two numbers sit about a fifth of a standard error apart. Of the
two, `seasonal_persistence` had the stronger evidence of undercoverage
(t = -2.15 against -1.89), because its day-to-day spread was tighter.
The t statistic counts the shortfall in standard errors, so more
negative is stronger evidence.
`har` appeared for two days and left. `seasonal_persistence` appeared
for four days and left. Nothing about those models had changed.

Since 2026-08-24 the check tests the evidence instead of the point estimate. It takes
each model's coverage one day at a time and runs a two-sided t-test of
those daily figures against 0.90, asking whether their average sits
farther from 0.90 than their own spread explains. It then divides the
5% level by the number of models tested (a Bonferroni correction),
because testing eight at once at an uncorrected 5% level produces a
false rejection often.
A model is reported only after it rejects on
three consecutive scored days. Earlier results are recomputed from
`evaluation.csv` rather than stored, so the whole check is reproducible
from the log with no state file that could drift out of step with the
data.

Replayed over every scored day, the check stayed silent through
2026-08-30, and not by a wide margin. `gbm` rejected on 2026-08-26 and
2026-08-27, `prophet` on 2026-08-27 and 2026-08-28, and each streak
broke one day short of the report line. A fresh `gbm` streak began on
2026-08-29. On 2026-08-31 the check reported a model for the first time,
naming `gbm` at a coverage of 0.7932 over its 28 scored days, a
p-value of 0.0058 against the corrected threshold of 0.0063. A p-value
is the chance of a gap that large, in either direction, arising from
noise alone. `gbm` was the model
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

## Limitations and next steps

The daily record is 49 scored days as of 2026-09-22, and the LIVE.md
results table will stay noisy until the sample grows.

The forecast log's timing evidence is the commit history, which I control.
The GitHub push history, recorded on GitHub's side, is an independent
record a reader can check it against. The loop missed 2026-09-02
entirely after an unplanned restart, and the 2026-09-03 forecast was
committed late, which LIVE.md lists.

The coverage columns in LIVE.md carry real uncertainty, because each day
contributes about 24 dependent hourly rows. The calibration check above
quantifies that uncertainty rather than reading the column as exact,
though it treats each scored day as independent of the last, and that
day-to-day dependence is unmodeled. As of 2026-09-18, six of the eight
models' coverage sits below 0.90 and the other two sit just above it.
That mostly one-sided pattern is a weak signal that the bands are
narrow, and no per-model test will settle it at this sample size. A
pattern like that is why the check was rebuilt rather than removed.

The 2026-08-19 forecast day shows the pattern of the whole record.
Realized volatility ran 3.67 times the nhits median forecast, and on
2026-08-21 the fixed-floor calibration check flagged five models below
its 0.80 coverage floor, its widest list. The forecast tracks the level
of ordinary days, and the rare day that breaks the
pattern is not signaled by the hours before it.

The volatility tournament is a single asset, and nothing here shows the
ranking holds on other coins or other markets. The load demo runs the
classical models only, without N-HiTS, so the cross-series comparison
covers seven models rather than eight. The remaining next step is
adding N-HiTS to the load demo.
