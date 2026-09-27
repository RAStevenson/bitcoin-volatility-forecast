"""Settings for the whole harness, covering repo paths and data source
ids, the quantile grid, the realized-volatility and backtest windows, and
the thresholds of the live calibration check. Every other fbench module
and every entry script in scripts/ reads its constants from here rather
than defining them locally."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"   # reports and the two live logs at the
                                 # top; backtest/ holds each backtest
                                 # run's rows and sidecar, figures/ the
                                 # figures the reports embed. The logs
                                 # stay at the top because the timing
                                 # audit reads forecasts.csv's history
                                 # by path.
HOURLY_PATH = DATA_DIR / "hourly_rv.csv"   # the committed hourly series

PRODUCT = "BTC-USD"            # Coinbase product id
BITSTAMP_PAIR = "btcusd"
HISTORY_START = "2023-08-01"   # ~3 years of 1-min candles at build time
MINUTE_SECONDS = 60
HOUR_SECONDS = 3600

QUANTILES = [0.05, 0.25, 0.50, 0.75, 0.95]
QCOLS = ["q05", "q25", "q50", "q75", "q95"]

HORIZON = 24                   # hourly steps per forecast
TRAIN_DAYS = 365               # persistence, HAR, Prophet, GBM
SARIMA_TRAIN_DAYS = 90         # SARIMAX cost grows fast with window
TEST_DAYS = 365                # backtest span
ORIGIN_STRIDE_DAYS = 2         # ~183 origins over TEST_DAYS

MIN_MINUTES_PER_HOUR = 45      # fewer 1-min returns -> hour is NaN
ANNUALIZER = (365 * 24) ** 0.5 # hourly variance -> annualized vol units

# Live calibration check. Hourly rows within a day are strongly
# dependent, so the effective sample is roughly the number of scored
# days, not the row count; no result is reported below the minimum.
MIN_CALIBRATION_DAYS = 10
COV90_TARGET = 0.90
# The check compares each model's day-level coverage against the target
# with a two-sided t-test, Bonferroni-corrected across the models tested,
# and reports a model only after it rejects on consecutive days. A fixed
# floor was tried first and could not separate a miscalibrated model from
# a noisy one: at ~20 scored days the standard error of day-level
# coverage is about 0.045, so a floor at 0.80 sat inside the noise. Its
# flag list stayed populated for nine straight days (one model the first
# four, three to five from 2026-08-20) and swapped members as point
# estimates drifted a few thousandths.
CALIBRATION_ALPHA = 0.05
CALIBRATION_PERSISTENCE_DAYS = 3
