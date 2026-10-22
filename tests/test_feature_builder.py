import numpy as np
import pandas as pd

from fbench.feature_builder import FEATURE_COLS, build_features


def _hourly(n_hours=2000, seed=0):
    timestamps = pd.date_range("2026-01-01", periods=n_hours, freq="h", tz="UTC")
    random_generator = np.random.default_rng(seed)
    return pd.DataFrame({"log_rv": random_generator.normal(0, 1, n_hours)},
                        index=timestamps)


def test_columns_present():
    features = build_features(_hourly())
    assert set(FEATURE_COLS) <= set(features.columns)


def test_features_use_nothing_past_their_own_hour():
    """Rewriting the series from hour 1000 on must leave every row before
    hour 1000 unchanged, and must change row 1000 itself, which is how a
    row that uses its own hour differs from one shifted a further hour
    back."""
    hourly = _hourly()
    features_before = build_features(hourly)
    hourly_rewritten = hourly.copy()
    hourly_rewritten.iloc[1000:, 0] = 999.0  # rewrite the future
    features_after = build_features(hourly_rewritten)
    last_unchanged_hour = hourly.index[999]
    first_rewritten_hour = hourly.index[1000]
    pd.testing.assert_frame_equal(features_before.loc[:last_unchanged_hour, FEATURE_COLS],
                                  features_after.loc[:last_unchanged_hour, FEATURE_COLS])
    assert not features_before.loc[first_rewritten_hour, FEATURE_COLS].equals(
        features_after.loc[first_rewritten_hour, FEATURE_COLS])


def test_lag_0_is_the_rows_own_hour():
    hourly = _hourly()
    features = build_features(hourly)
    pd.testing.assert_series_equal(features["lag_0"], hourly["log_rv"], check_names=False)
    assert features["lag_1"].iloc[500] == hourly["log_rv"].iloc[499]
    assert features["lag_24"].iloc[500] == hourly["log_rv"].iloc[476]


def test_har_d_matches_manual_mean():
    hourly = _hourly()
    features = build_features(hourly)
    manual_mean = hourly["log_rv"].to_numpy()[477:501].mean()  # 24 hours ending at row 500
    assert abs(features["har_d"].to_numpy()[500] - manual_mean) < 1e-12
