import numpy as np
import pandas as pd

from fbench.feature_builder import FEATURE_COLS, build_features


def _hourly(n_hours=2000, seed=0):
    timestamps = pd.date_range("2026-01-01", periods=n_hours, freq="h", tz="UTC")
    rng = np.random.default_rng(seed)
    return pd.DataFrame({"log_rv": rng.normal(0, 1, n_hours)}, index=timestamps)


def test_columns_present():
    features = build_features(_hourly())
    assert set(FEATURE_COLS) <= set(features.columns)


def test_features_are_strictly_trailing():
    hourly = _hourly()
    features_before = build_features(hourly)
    hourly_rewritten = hourly.copy()
    hourly_rewritten.iloc[1000:, 0] = 999.0  # rewrite the future
    features_after = build_features(hourly_rewritten)
    cut = hourly.index[999]
    pd.testing.assert_frame_equal(features_before.loc[:cut, FEATURE_COLS],
                                  features_after.loc[:cut, FEATURE_COLS])


def test_har_d_matches_manual_mean():
    hourly = _hourly()
    features = build_features(hourly)
    manual = hourly["log_rv"].to_numpy()[476:500].mean()  # 24 hours ending before row 500
    assert abs(features["har_d"].to_numpy()[500] - manual) < 1e-12
