# volatility-forecast-harness

A benchmarking harness for volatility forecasts. Model families from
naive persistence to a deep net produce next-24-hour quantile forecasts of
hourly realized volatility for BTC-USD, a predicted low/median/high band
rather than a single number.
Evaluation is rolling-origin temporal validation, where the forecast origin
steps forward through time and each forecast sees only data before it, with
quantile accuracy (pinball loss) and calibration (how often the truth lands
inside the band) scored separately. Every model must beat two honest
baselines, persistence and the HAR (heterogeneous autoregressive)
regression standard in volatility work, or the report says so.

In the pinned 2026-08-05 backtest, the best entrant (N-HiTS, the deep
net) scored a mean pinball loss of 0.0959 against 0.1180 for the
persistence baseline, a skill score of 0.186, meaning it removed about a
fifth of the baseline's error, averaged over forecast horizons of 1 to 24
hours. The current tournament results, figures, and dataset summary are in
[results/REPORT.md](results/REPORT.md) (generated, never hand-edited).

## Why

My private trading research system has a standing rule that no forecast
ships until it beats a classical baseline out of sample. This repo is that
discipline as a standalone, reusable harness on public data. The harness is
series-agnostic within its hourly frame. Models implement a small adapter
(train window in, quantile forecasts out), and any hourly series with a
timestamp index plugs in; the load demo below is the demonstration.

## Data

The data comes from public, keyless exchange APIs. Coinbase Exchange 1-minute candles are the
primary source, three years of them and growing daily; Bitstamp hourly
closes cross-check them (26,363 hours compared, median divergence 0.009%,
measured 2026-08-03, recorded in results/crosscheck.txt). Hourly realized
volatility is computed from 1-minute log returns, annualized, with hours
missing more than a quarter of their minutes marked NaN rather than treated
as quiet. Raw data is not committed; the backfill resumes from its last
saved candle and rebuilds the dataset from the exchanges.

## Models

| entrant | family |
|---|---|
| persistence, seasonal persistence | naive baselines |
| HAR (plain and hour-of-day seasonal) | econometric baseline (Corsi-style) |
| SARIMAX (1,0,1)(1,0,1,24) | classical seasonal time series |
| Prophet | Fourier daily/weekly seasonality |
| XGBoost | gradient boosting, native quantile objective |
| N-HiTS | deep learning (pytorch-forecasting), native quantile loss |

A second dataset, German hourly load (OPSD/ENTSO-E, CC-BY 4.0), runs
through the identical engine as a generality demo:
[results/LOAD_REPORT.md](results/LOAD_REPORT.md). The model ranking
reorders sharply against the volatility tournament, with Prophet climbing
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
python scripts/run_daily.py        # the live loop: score yesterday, log
                                   #   today, write results/REVIEW.md
                                   #   (yesterday's forecast vs realized),
                                   #   LIVE.md and OUTLOOK.md, commit
python scripts/run_verify_timing.py  # audit the live log's evidence claim
                                     #   against git history: exits 1 if any
                                     #   forecast row was first committed
                                     #   after its target hour completed
```

`run_vol_backtest.py` takes `--models`, `--stride`, and `--test-days` to run
subsets quickly, and `--no-report` to stop after writing the backtest
parquet. `run_load_demo.py` takes `--stride` (default 4) and `--test-days`
(default 365) with the same meanings. Experiment tracking is local MLflow (sqlite backend). Run
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
coverage has no spread gets no verdict at all.

## The calibration check

`LIVE.md` carries a `cov90` column, the fraction of hours where the
realized value landed inside a model's 90% band. A calibrated model
sits near 0.90, and a model that sits well below it is claiming more
precision than it has.

The first version of the check compared that column against a fixed
floor of 0.80 (the band also had a 0.98 ceiling no model ever
approached) and named anything underneath. From 2026-08-16 to
2026-08-24 it named `gbm` every day, and from 2026-08-20 on the list
grew to three to five of the eight models. The list never emptied, so
the check carried no information. A signal that is always on cannot
tell you when something changed.

The problem was that the floor sat inside the noise. Hourly rows within
a day are strongly dependent, so the effective sample is the number of
scored days, not the row count. At 21 scored days the standard error
of a typical model's day-level coverage, the noise expected in that
average from 21 days alone, is about 0.045. The gap between the 0.80
floor and the 0.90 target is roughly two standard errors wide, so a
perfectly calibrated model crosses it routinely. The membership of the
flagged list showed exactly that. On 2026-08-24, `seasonal_persistence`
left the list at 0.8056 while `har_seasonal` stayed on it at 0.7956.
Those two numbers sit about a fifth of a standard error apart. Of the
two, `seasonal_persistence` had the stronger evidence of undercoverage
(t = -2.15 against -1.89), because its day-to-day spread was tighter.
`har` appeared for two days and left. `seasonal_persistence` appeared
for four days and left. Nothing about those models had changed.

The check now tests the evidence instead of the point estimate. It takes
each model's coverage one day at a time and runs a two-sided t-test of
those daily figures against 0.90, asking whether their average sits
farther from 0.90 than their own spread explains. It then applies a
Bonferroni correction across the models tested, because testing eight
at once at an uncorrected 5% level produces false rejections routinely.
A model is reported only after it rejects on
three consecutive scored days. Earlier verdicts are recomputed from
`evaluation.csv` rather than stored, so the whole check is reproducible
from the log with no state file that could drift out of step with the
data.

Replayed over every scored day, the new check has never fired. It is not
silent by construction, though. At the current day-to-day spread it
reports a model whose 90% band is really covering about 0.76 or less.
`gbm` at 0.7798 sits 0.018 above its own firing point, closer than any
other model. Its closest approach so far came on 2026-08-18, a p-value
of 0.0108 against a corrected threshold of 0.0063. What changed is how
that number reads. `gbm` is now the model to watch, not an announced
failure.

The check stays silent in two cases on purpose. A model with fewer than
10 scored days gets no verdict, because three clean quiet days once
produced a coverage of 1.0 from models the year-long backtest shows are
calibrated. A model whose daily coverage has no spread at all also gets
none, because the test would have no uncertainty to divide by, and
inventing one would repeat the mistake the fixed floor made.

## Limitations and next steps

The live log is young, 21 scored days as of 2026-08-24, so the LIVE.md
leaderboard will stay noisy until the sample grows. Its coverage
columns carry real uncertainty, because each day contributes about 24
dependent hourly rows. The calibration check above quantifies that
uncertainty rather than reading the column as exact. The load demo runs the classical models only, without N-HiTS,
so the cross-series comparison covers seven entrants rather than eight.
The volatility tournament is a single asset, and nothing here shows the
ranking holds on other coins or other markets. Every model's coverage
sits below 0.90, none above. That one-sided pattern across all eight is
a weak but real signal that the bands are narrow, and no per-model test
will settle it at this sample size. It is the reason the check was
rebuilt rather than removed. The fixed-floor calibration check first
flagged five models below the 0.80 coverage floor on 2026-08-21, after a
2026-08-19 forecast day whose realized volatility ran 3.67 times the
nhits median forecast. I replayed an adaptive conformal layer (a
band-widening rule driven by recent coverage misses) over the 18 scored
days then available. It lifted every flagged model above the floor at
no pinball cost. But it widened the 08-19 band by almost nothing,
because the two days before it were clean and the rule reacts only to
misses it has seen. It was not adopted. The bands stay as each model
produces them, and the coverage column is the honest record of that.
The fixed floor was replaced on 2026-08-24 by the evidence-based check
described above, after its list had stayed populated for nine
consecutive days without that membership meaning anything. The
remaining next step is adding N-HiTS to the load demo.
