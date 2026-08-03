import numpy as np
import pandas as pd
import pytest

import fbench.models.har  # noqa: F401  (registers)
import fbench.models.persistence  # noqa: F401
from fbench.config import HORIZON, QCOLS
from fbench.features import build_features
from fbench.models.base import REGISTRY


def _train(n=24 * 400, seed=1):
    idx = pd.date_range("2025-01-01", periods=n, freq="h", tz="UTC")
    rng = np.random.default_rng(seed)
    lr = pd.Series(rng.normal(0, 0.3, n), index=idx).rolling(3).mean()
    return build_features(pd.DataFrame({"log_rv": lr}))


@pytest.mark.parametrize("name", sorted(REGISTRY))
def test_contract(name):
    train = _train()
    future = pd.date_range(train.index[-1] + pd.Timedelta(hours=1),
                           periods=HORIZON, freq="h", tz="UTC")
    m = REGISTRY[name]()
    m.fit(train)
    out = m.predict(future)
    assert list(out.columns) == QCOLS
    assert out.index.equals(future)
    assert out.notna().all().all()
    assert (out.values[:, :-1] <= out.values[:, 1:]).all()  # monotone
