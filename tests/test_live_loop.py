import numpy as np
import pandas as pd
import pytest

import fbench.models.persistence_model  # noqa: F401  (registers baselines only)
from fbench import live_loop
from fbench.feature_builder import build_features


@pytest.fixture
def logs_in_tmp(tmp_path, monkeypatch):
    monkeypatch.setattr(live_loop, "FORECAST_LOG", tmp_path / "forecasts.csv")
    monkeypatch.setattr(live_loop, "EVAL_LOG", tmp_path / "evaluation.csv")
    monkeypatch.setattr(live_loop, "RESULTS_DIR", tmp_path)
    return tmp_path


def _frame(n=24 * 400, seed=3):
    idx = pd.date_range("2025-01-01", periods=n, freq="h", tz="UTC")
    rng = np.random.default_rng(seed)
    lr = pd.Series(rng.normal(0, 0.3, n), index=idx).rolling(3).mean()
    return pd.DataFrame({"log_rv": lr, "rv": np.exp(lr)}, index=idx)


def test_log_forecasts_is_idempotent_per_origin(logs_in_tmp):
    h = _frame()
    feats = build_features(h)
    origin = h.index[-30]  # leave future hours unobserved
    first = live_loop.log_forecasts(feats, origin)
    assert first > 0
    again = live_loop.log_forecasts(feats, origin)
    assert again == 0


def test_score_due_resolves_only_observed_hours(logs_in_tmp):
    h = _frame()
    feats = build_features(h)
    origin = h.index[-13]  # only 12 of 24 target hours observed
    live_loop.log_forecasts(feats, origin)
    n_models = len(pd.read_csv(live_loop.FORECAST_LOG)["model"].unique())
    resolved = live_loop.score_due(h)
    assert resolved == 12 * n_models
    assert live_loop.score_due(h) == 0  # second pass appends nothing


def test_score_due_waits_for_the_hour_to_end(logs_in_tmp):
    h = _frame()
    feats = build_features(h)
    origin = h.index[-30]
    live_loop.log_forecasts(feats, origin)
    n_models = len(pd.read_csv(live_loop.FORECAST_LOG)["model"].unique())
    # every target hour has an actual, but only the hours that have ENDED
    # by the clock may resolve: targets origin+1h .. origin+12h end by
    # origin+13h, the 13th is still in progress
    resolved = live_loop.score_due(h, now=origin + pd.Timedelta(hours=13))
    assert resolved == 12 * n_models


def test_logs_are_appended_not_rewritten(logs_in_tmp):
    h = _frame()
    feats = build_features(h)
    live_loop.log_forecasts(feats, h.index[-60])
    first = live_loop.FORECAST_LOG.read_bytes()
    live_loop.log_forecasts(feats, h.index[-30])
    second = live_loop.FORECAST_LOG.read_bytes()
    assert second.startswith(first)  # the earlier bytes are untouched
    assert second.count(b"\n") > first.count(b"\n")


def test_day_level_scores_reward_the_right_day_average():
    idx = pd.date_range("2026-01-01 01:00", periods=48, freq="h", tz="UTC")
    origins = [idx[0] - pd.Timedelta(hours=1), idx[24] - pd.Timedelta(hours=1)]
    rows = []
    for o, block in zip(origins, (idx[:24], idx[24:])):
        y = np.linspace(-1.2, -0.8, 24)
        for model, offset in (("exact", 0.0), ("persistence", 0.3)):
            for k, t in enumerate(block):
                rows.append({"origin": o, "target_time": t, "horizon": k + 1,
                             "model": model, "q05": y[k] - 1, "q25": y[k] - .5,
                             "q50": y[k] + offset, "q75": y[k] + .5,
                             "q95": y[k] + 1, "y_true": y[k]})
    d = live_loop.day_level_scores(pd.DataFrame(rows))
    assert d.loc["exact", "day_error"] == pytest.approx(0.0)
    assert d.loc["persistence", "day_error"] == pytest.approx(0.3)
    assert d.loc["exact", "day_skill"] == pytest.approx(1.0)
    assert d.loc["persistence", "day_skill"] == pytest.approx(0.0)


def test_live_report_written(logs_in_tmp):
    h = _frame()
    feats = build_features(h)
    live_loop.log_forecasts(feats, h.index[-25])
    live_loop.score_due(h)
    path = live_loop.write_live_report()
    text = path.read_text()
    assert "persistence" in text and "pinball" in text
    # one scored day -> the calibration check must be gated, not verdicted
    assert "calibration check stays inactive" in text
    assert "day_error" in text and (logs_in_tmp / "fig_live_daily.png").exists()


def _ev(cov_by_model, start="2026-01-01"):
    """Synthetic evaluation log. cov_by_model maps a model to its list of
    per-day coverage fractions; each day is 24 hourly rows and the first
    round(24 * frac) of them are placed inside the band."""
    rows = []
    for model, fracs in cov_by_model.items():
        for d, frac in enumerate(fracs):
            origin = pd.Timestamp(start, tz="UTC") + pd.Timedelta(days=d)
            inside = round(24 * frac)
            for h in range(24):
                rows.append({
                    "origin": origin, "horizon": h + 1,
                    "target_time": origin + pd.Timedelta(hours=h + 1),
                    "model": model, "q05": 0.0, "q25": 0.0, "q50": 0.5,
                    "q75": 1.0, "q95": 1.0,
                    "y_true": 0.5 if h < inside else 5.0,
                })
    return pd.DataFrame(rows)


def _lines(cov_by_model):
    ev = _ev(cov_by_model)
    return live_loop.calibration_lines(ev, ev["origin"].dt.date.nunique())


def test_calibration_gated_below_min_days():
    lines = _lines({"a": [1.0] * 3})
    assert "inactive" in lines[0]
    assert "3 so far" in lines[0]


def test_calibration_passes_when_coverage_is_at_target():
    # jitter around 0.90 so the day-level spread is real but centred
    cov = [0.875, 0.917, 0.875, 0.917, 0.958, 0.833, 0.917, 0.875,
           0.958, 0.875, 0.917, 0.833, 0.875, 0.917]
    lines = _lines({"a": cov})
    assert "passes" in lines[0]
    assert "Bonferroni-corrected" in lines[0]


def test_calibration_flags_a_persistently_miscalibrated_model():
    # far enough below target that the corrected test rejects on each of
    # the last three days, not just the latest one
    lines = _lines({"a": [0.500, 0.542, 0.458, 0.500, 0.583, 0.458, 0.500,
                          0.542, 0.500, 0.458, 0.542, 0.500, 0.583, 0.500]})
    assert "flags" in lines[0]
    assert "a cov90 0.5" in lines[0]


def test_rejection_short_of_the_streak_is_not_reported():
    """The regression this change exists for. This model rejects the
    corrected test today and again on the window ending yesterday, but
    not the day before that, so it is reported as pending rather than
    flagged."""
    cov = [0.875, 0.875, 0.917, 0.792, 0.750, 0.917,
           0.917, 0.917, 0.833, 0.792, 0.792, 0.708]
    ev = _ev({"a": cov})
    assert live_loop.coverage_verdicts(ev)["a"]["reject"]
    assert live_loop.rejection_streaks(ev) == {"a": 2}
    lines = live_loop.calibration_lines(ev, ev["origin"].dt.date.nunique())
    assert "passes" in lines[0]
    assert "day 2 of 3" in lines[0]


def test_no_verdict_when_daily_coverage_has_no_spread():
    """Zero spread leaves the test no uncertainty to divide by, so the
    model gets no verdict rather than an invented one."""
    ev = _ev({"a": [1.0] * 14})
    assert live_loop.coverage_verdicts(ev) == {}


def test_correction_is_applied_across_models_tested():
    cov = [0.917, 0.875, 0.917, 0.875, 0.958, 0.875, 0.917,
           0.875, 0.917, 0.958, 0.875, 0.917, 0.875, 0.917]
    one = live_loop.coverage_verdicts(_ev({"a": cov}))
    four = live_loop.coverage_verdicts(
        _ev({"a": cov, "b": cov, "c": cov, "d": cov}))
    assert one["a"]["alpha"] == pytest.approx(0.05)
    assert four["a"]["alpha"] == pytest.approx(0.05 / 4)


def test_models_below_min_days_are_not_tested():
    cov = [0.917, 0.875, 0.917, 0.875, 0.958, 0.875, 0.917,
           0.875, 0.917, 0.958, 0.875, 0.917, 0.875, 0.917]
    v = live_loop.coverage_verdicts(_ev({"a": cov, "young": cov[:5]}))
    assert "a" in v and "young" not in v
