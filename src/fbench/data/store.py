import pandas as pd

from fbench.config import DATA_DIR, PRODUCT


def minute_path():
    return DATA_DIR / f"minute_{PRODUCT}.parquet"


def load_minutes():
    p = minute_path()
    if not p.exists():
        return pd.DataFrame()
    return pd.read_parquet(p)


def save_minutes(df):
    DATA_DIR.mkdir(exist_ok=True)
    df.to_parquet(minute_path(), index=False)


def gap_report(df, granularity_seconds):
    """Count and locate missing bars against a complete regular grid."""
    full = pd.date_range(df["time"].min(), df["time"].max(),
                         freq=f"{granularity_seconds}s", tz="UTC")
    missing = full.difference(pd.DatetimeIndex(df["time"]))
    return {"expected": len(full), "present": len(df),
            "missing": len(missing),
            "missing_sample": list(missing[:10].astype(str))}
