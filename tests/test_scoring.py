import pandas as pd

from fbench.scoring import pinball, score


def test_pinball_hand_values():
    # y=1, q=0, alpha=0.5 -> 0.5 ; alpha=0.05 under-forecast -> 0.05
    assert pinball([1.0], [0.0], 0.5) == 0.5
    assert abs(pinball([1.0], [0.0], 0.05) - 0.05) < 1e-12
    # over-forecast: y=0, q=1, alpha=0.05 -> 0.95
    assert abs(pinball([0.0], [1.0], 0.05) - 0.95) < 1e-12


def test_nan_forecast_rows_are_excluded_not_poisonous():
    df = pd.DataFrame({
        "origin": pd.Timestamp("2026-01-01", tz="UTC"),
        "target_time": pd.date_range("2026-01-01 01:00", periods=4,
                                     freq="h", tz="UTC"),
        "horizon": [1, 1, 2, 2], "model": "m",
        "q05": [0.9, None, 0.9, None], "q25": 0.95,
        "q50": [1.0, None, 1.0, None], "q75": 1.05,
        "q95": [1.1, None, 1.1, None],
        "y_true": 1.0,
    })
    s = score(df)
    assert (s["n"] == 1).all()          # NaN rows dropped, visible in n
    assert s["pinball_mean"].notna().all()


def test_score_perfect_forecast():
    df = pd.DataFrame({
        "origin": pd.Timestamp("2026-01-01", tz="UTC"),
        "target_time": pd.date_range("2026-01-01 01:00", periods=4,
                                     freq="h", tz="UTC"),
        "horizon": [1, 2, 3, 4], "model": "m",
        "q05": 0.9, "q25": 0.95, "q50": 1.0, "q75": 1.05, "q95": 1.1,
        "y_true": 1.0,
    })
    s = score(df)
    assert (s["mae"] == 0).all() and (s["cov90"] == 1).all()
