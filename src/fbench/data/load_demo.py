"""German hourly electricity load from Open Power System Data, the
out-of-domain series used to show the engine is not tied to crypto."""

import numpy as np
import pandas as pd

from fbench.config import DATA_DIR

# Open Power System Data time-series package (final 2020-10-06 release),
# hourly load for Germany from ENTSO-E Transparency. Keyless download;
# attribution: Open Power System Data / ENTSO-E, CC-BY 4.0. The file is
# ~250 MB but usecols keeps the parse to two columns.
OPSD_URL = ("https://data.open-power-system-data.org/time_series/"
            "2020-10-06/time_series_60min_singleindex.csv")
SERIES = "DE_load_actual_entsoe_transparency"
LOAD_PATH = DATA_DIR / "hourly_load_DE.parquet"


def fetch_load(url=OPSD_URL):
    """Build the load demo frame in the harness's engine schema.

    The engine's target column is named log_rv for its original domain;
    it is treated everywhere as an arbitrary log-scale hourly series, so
    the load demo maps log(MW) into it. `rv` carries the raw MW level
    for the report's hourly-profile figure.
    """
    df = pd.read_csv(url, usecols=["utc_timestamp", SERIES])
    df["time"] = pd.to_datetime(df["utc_timestamp"], utc=True)
    s = df.set_index("time")[SERIES].astype(float).dropna()
    full = pd.date_range(s.index.min(), s.index.max(), freq="h", tz="UTC")
    s = s.reindex(full)
    out = pd.DataFrame({"rv": s, "log_rv": np.log(s)})
    DATA_DIR.mkdir(exist_ok=True)
    out.to_parquet(LOAD_PATH)
    return out
