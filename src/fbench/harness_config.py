"""Settings for the whole harness, covering repo paths and data source
ids, the quantile grid, the realized-volatility and backtest windows, and
the live record's origin hour and minimum sample, and the release origin
that dates the current model settings. A constant that
belongs to one module's job is defined in that module instead, such as
FALLBACK_MODEL in daily_forecast_generator, LATE_COMMIT_REASONS in
commit_timing, and ON_TARGET in review_generator."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"   # reports and the two live logs at the
                                 # top; backtest/ holds each backtest
                                 # run's rows and sidecar, figures/ the
                                 # figures the reports embed, tuning/
                                 # the grid-search scores. The logs
                                 # stay at the top because the timing
                                 # audit reads forecasts.csv's history
                                 # by path.
HOURLY_PATH = DATA_DIR / "hourly_rv.csv"   # the committed hourly series

PRODUCT = "BTC-USD"            # Coinbase product id
HISTORY_START = "2023-08-01"   # ~3 years of 1-min candles at build time
MINUTE_SECONDS = 60

QUANTILES = [0.05, 0.25, 0.50, 0.75, 0.95]
QCOLS = ["q05", "q25", "q50", "q75", "q95"]

HORIZON = 24                   # hourly steps per forecast
TRAIN_DAYS = 365               # persistence, HAR, Prophet, GBM, N-HiTS
SARIMA_TRAIN_DAYS = 90         # SARIMAX cost grows fast with window
TEST_DAYS = 365                # backtest span
ORIGIN_STRIDE_DAYS = 2         # ~183 origins over TEST_DAYS

MIN_MINUTES_PER_HOUR = 45      # fewer 1-min returns -> hour is NaN
ORIGIN_HOUR_UTC = 10           # the daily run's origin, the same clock
                               # hour every day whatever minute the run
                               # starts, so a late start forecasts the
                               # same window and sees no data past it
ANNUALIZER = (365 * 24) ** 0.5 # hourly variance -> annualized vol units

# Fewest fully resolved days the leader and persistence must share
# before LIVE.md states the leader's matched-day skill and its interval.
# Hourly rows within a day are strongly dependent, so the effective
# sample is the day count, not the row count.
MIN_MATCHED_DAYS = 10

# The first forecast origin made on the current model settings, set in
# the release that changed them. LIVE.md counts the days scored since it.
# The forecast page and the review build their day figure from each
# hour's expected volatility from this origin on and from the median
# before it, so a past day is scored by the rule its own page printed.
RELEASE_ORIGIN = "2026-10-23 10:00"   # UTC, the first forecast origin after the release landed
