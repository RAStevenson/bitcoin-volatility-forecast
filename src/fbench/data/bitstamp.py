import time

import pandas as pd
import requests

BASE = "https://www.bitstamp.net/api/v2/ohlc"
LIMIT = 1000


def fetch_hourly(pair, start, end):
    out = []
    cur = int(start.timestamp())
    end_s = int(end.timestamp())
    while cur < end_s:
        r = requests.get(f"{BASE}/{pair}/",
                         params={"step": 3600, "limit": LIMIT, "start": cur},
                         timeout=30)
        r.raise_for_status()
        rows = r.json()["data"]["ohlc"]
        if not rows:
            break
        out.extend(rows)
        cur = int(rows[-1]["timestamp"]) + 3600
        time.sleep(0.2)
    df = pd.DataFrame(out)
    df["time"] = pd.to_datetime(df["timestamp"].astype(int), unit="s",
                                utc=True)
    df["close"] = df["close"].astype(float)
    return (df[["time", "close"]].drop_duplicates("time")
            .sort_values("time").reset_index(drop=True))
