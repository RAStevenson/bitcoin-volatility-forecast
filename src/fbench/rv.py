import numpy as np
import pandas as pd

from fbench.config import ANNUALIZER, MIN_MINUTES_PER_HOUR


def hourly_realized_vol(minute_close):
    """Hourly realized vol from 1-min closes.

    rv = sqrt(sum of squared 1-min log returns in the hour), annualized.
    Hours with fewer than MIN_MINUTES_PER_HOUR returns are NaN rather than
    silently quiet: a data gap must not masquerade as low volatility.
    """
    r = np.log(minute_close).diff().dropna()
    hour = r.index.floor("h")
    ss = r.pow(2).groupby(hour).sum()
    n = r.groupby(hour).count()
    out = pd.DataFrame({"rv": np.sqrt(ss) * ANNUALIZER, "n_minutes": n})
    out.loc[out["n_minutes"] < MIN_MINUTES_PER_HOUR, "rv"] = np.nan
    out["log_rv"] = np.log(out["rv"])
    full = pd.date_range(out.index.min(), out.index.max(), freq="h", tz="UTC")
    return out.reindex(full)  # absent hours become explicit NaN rows
