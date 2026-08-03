import pandas as pd

from fbench.config import HORIZON
from fbench.models.base import REGISTRY


def make_origins(index, test_days, stride_days):
    last_full = index[-1].floor("D")
    start = last_full - pd.Timedelta(days=test_days)
    return pd.date_range(start, last_full - pd.Timedelta(days=1),
                         freq=f"{stride_days}D", tz="UTC")


def run_backtest(feats, model_names, origins, horizon=HORIZON):
    out = []
    for origin in origins:
        future = pd.date_range(origin + pd.Timedelta(hours=1),
                               periods=horizon, freq="h", tz="UTC")
        for name in model_names:
            cls = REGISTRY[name]
            train = feats.loc[origin - pd.Timedelta(days=cls.train_days):
                              origin]
            # The two guards below ARE the leakage policy. Never remove.
            assert train.index.max() <= origin
            assert future.min() > origin
            m = cls()
            m.fit(train)
            q = m.predict(future)
            q = q.assign(origin=origin, model=name,
                         horizon=range(1, horizon + 1),
                         y_true=feats["log_rv"].reindex(future).to_numpy())
            out.append(q.rename_axis("target_time").reset_index())
    return pd.concat(out, ignore_index=True)
