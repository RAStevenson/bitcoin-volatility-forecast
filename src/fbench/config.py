from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"

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
# days, not the row count; no verdict is issued below the minimum.
MIN_CALIBRATION_DAYS = 10
COV90_BAND = (0.80, 0.98)
