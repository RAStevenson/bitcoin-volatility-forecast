import numpy as np
import pandas as pd

from fbench.feature_builder import FEATURE_COLS, build_features


def _hourly(n=2000, seed=0):
    idx = pd.date_range("2026-01-01", periods=n, freq="h", tz="UTC")
    rng = np.random.default_rng(seed)
    return pd.DataFrame({"log_rv": rng.normal(0, 1, n)}, index=idx)


def test_columns_present():
    f = build_features(_hourly())
    assert set(FEATURE_COLS) <= set(f.columns)


def test_features_are_strictly_trailing():
    h = _hourly()
    f1 = build_features(h)
    h2 = h.copy()
    h2.iloc[1000:, 0] = 999.0  # rewrite the future
    f2 = build_features(h2)
    cut = h.index[999]
    pd.testing.assert_frame_equal(f1.loc[:cut, FEATURE_COLS],
                                  f2.loc[:cut, FEATURE_COLS])


def test_har_d_matches_manual_mean():
    h = _hourly()
    f = build_features(h)
    manual = h["log_rv"].to_numpy()[476:500].mean()  # 24 hours ending before row 500
    assert abs(f["har_d"].to_numpy()[500] - manual) < 1e-12
