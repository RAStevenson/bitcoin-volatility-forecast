# volatility-forecast-harness

A benchmarking harness for volatility forecasts. Five model families
produce next-24-hour quantile forecasts of hourly realized volatility for
BTC-USD, evaluated under rolling-origin temporal validation with pinball
loss and calibration coverage scored separately. Every model must beat two
honest baselines (persistence and HAR) or the report says so.

The current tournament results, figures, and dataset summary are in
[results/REPORT.md](results/REPORT.md) (generated, never hand-edited).

## Why

My private trading research system has a standing rule: no forecast ships
until it beats a classical baseline out of sample. This repo is that
discipline as a standalone, reusable harness on public data. The harness is
series-agnostic: models implement a small adapter (train window in, quantile
forecasts out) and anything with a timestamp index plugs in.

## Data

Public, keyless exchange APIs. Coinbase Exchange 1-minute candles are the
primary source (3 years, ~1.58M rows); Bitstamp hourly closes cross-check
them (26,363 hours compared, median divergence 0.009%). Hourly realized
volatility is computed from 1-minute log returns, annualized, with hours
missing more than a quarter of their minutes marked NaN rather than treated
as quiet. Raw data is not committed; every run script is resumable and
rebuilds it from the exchanges.

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
inverts against the volatility tournament, which is the point: model
family choice depends on series structure, and the harness measures it.

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
subsets quickly. Experiment tracking is local MLflow (sqlite backend);
`mlflow ui --backend-store-uri sqlite:///mlflow.db` to browse runs.

Prophet on Windows: the pip wheel worked as-is here (cmdstanpy backend,
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
