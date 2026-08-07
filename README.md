# volatility-forecast-harness

A benchmarking harness for volatility forecasts. Model families from
naive persistence to a deep net produce next-24-hour quantile forecasts of
hourly realized volatility for BTC-USD, a predicted low/median/high band
rather than a single number.
Evaluation is rolling-origin temporal validation, where the forecast origin
steps forward through time and each forecast sees only data before it, with
quantile accuracy (pinball loss) and calibration (how often the truth lands
inside the band) scored separately. Every model must beat two honest
baselines, persistence and the HAR regression standard in volatility work,
or the report says so.

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
series-agnostic. Models implement a small adapter (train window in, quantile
forecasts out), and anything with a timestamp index plugs in.

## Data

The data comes from public, keyless exchange APIs. Coinbase Exchange 1-minute candles are the
primary source (3 years, ~1.58M rows); Bitstamp hourly closes cross-check
them (26,363 hours compared, median divergence 0.009%). Hourly realized
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
from next-to-last to second, which is the point. Model family choice
depends on series structure, and the harness measures it.

## Setup and run

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

python scripts/run_backfill.py     # fetch 1-min candles (resumable)
python scripts/run_crosscheck.py   # verify against Bitstamp
python scripts/run_build_rv.py     # build the hourly realized-vol series
python scripts/run_backtest.py     # rolling-origin tournament
python scripts/run_report.py       # score, log to MLflow, write REPORT.md
```

`run_backtest.py` takes `--models`, `--stride`, and `--test-days` to run
subsets quickly. Experiment tracking is local MLflow (sqlite backend). Run
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
never shows a model data past its origin.

## Limitations and next steps

The live log is young, four scored days as of 2026-08-07, so the LIVE.md
leaderboard will stay noisy until the sample grows, and its coverage
columns are provisional because each day contributes about 24 dependent
hourly rows. The load demo runs the classical models only, without N-HiTS,
so the cross-series comparison covers seven entrants rather than eight.
The volatility tournament is a single asset, and nothing here shows the
ranking holds on other coins or other markets. The next steps are letting
the live log accumulate toward its 10-day calibration check and adding
N-HiTS to the load demo.
