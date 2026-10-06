import numpy as np
import pandas as pd
import pytest

import fbench.models.persistence_model  # noqa: F401  (registers baselines only)
from fbench import daily_run
from fbench.feature_builder import build_features


@pytest.fixture
def logs_in_tmp(tmp_path, monkeypatch):
    monkeypatch.setattr(daily_run, "FORECAST_LOG", tmp_path / "forecasts.csv")
    monkeypatch.setattr(daily_run, "EVAL_LOG", tmp_path / "evaluation.csv")
    monkeypatch.setattr(daily_run, "RESULTS_DIR", tmp_path)
    return tmp_path


def _frame(n_hours=24 * 400, seed=3):
    idx = pd.date_range("2025-01-01", periods=n_hours, freq="h", tz="UTC")
    rng = np.random.default_rng(seed)
    log_realized_vol = (pd.Series(rng.normal(0, 0.3, n_hours), index=idx)
                        .rolling(3).mean())
    return pd.DataFrame({"log_rv": log_realized_vol, "rv": np.exp(log_realized_vol)},
                        index=idx)


def test_log_forecasts_is_idempotent_per_origin(logs_in_tmp):
    hourly = _frame()
    feats = build_features(hourly)
    origin = hourly.index[-30]  # leave future hours unobserved
    first = daily_run.log_forecasts(feats, origin)
    assert first > 0
    again = daily_run.log_forecasts(feats, origin)
    assert again == 0


def test_score_due_resolves_only_observed_hours(logs_in_tmp):
    hourly = _frame()
    feats = build_features(hourly)
    origin = hourly.index[-13]  # only 12 of 24 target hours observed
    daily_run.log_forecasts(feats, origin)
    n_models = len(pd.read_csv(daily_run.FORECAST_LOG)["model"].unique())
    resolved = daily_run.score_due(hourly)
    assert resolved == 12 * n_models
    assert daily_run.score_due(hourly) == 0  # second pass appends nothing


def test_score_due_waits_for_the_hour_to_end(logs_in_tmp):
    hourly = _frame()
    feats = build_features(hourly)
    origin = hourly.index[-30]
    daily_run.log_forecasts(feats, origin)
    n_models = len(pd.read_csv(daily_run.FORECAST_LOG)["model"].unique())
    # every target hour has an actual, but only the hours that have ENDED
    # by the clock may resolve: targets origin+1h .. origin+12h end by
    # origin+13h, the 13th is still in progress
    resolved = daily_run.score_due(hourly, now=origin + pd.Timedelta(hours=13))
    assert resolved == 12 * n_models


def test_logs_are_appended_not_rewritten(logs_in_tmp):
    hourly = _frame()
    feats = build_features(hourly)
    daily_run.log_forecasts(feats, hourly.index[-60])
    first = daily_run.FORECAST_LOG.read_bytes()
    daily_run.log_forecasts(feats, hourly.index[-30])
    second = daily_run.FORECAST_LOG.read_bytes()
    assert second.startswith(first)  # the earlier bytes are untouched
    assert second.count(b"\n") > first.count(b"\n")


def test_day_level_scores_reward_the_right_day_average():
    idx = pd.date_range("2026-01-01 01:00", periods=48, freq="h", tz="UTC")
    origins = [idx[0] - pd.Timedelta(hours=1), idx[24] - pd.Timedelta(hours=1)]
    rows = []
    for origin, block in zip(origins, (idx[:24], idx[24:]), strict=True):
        truth = np.linspace(-1.2, -0.8, 24)
        for model, offset in (("exact", 0.0), ("persistence", 0.3)):
            for i, target_time in enumerate(block):
                rows.append({"origin": origin, "target_time": target_time,
                             "horizon": i + 1, "model": model,
                             "q05": truth[i] - 1, "q25": truth[i] - .5,
                             "q50": truth[i] + offset, "q75": truth[i] + .5,
                             "q95": truth[i] + 1, "y_true": truth[i]})
    scores = daily_run.day_level_scores(pd.DataFrame(rows))
    assert scores.loc["exact", "day_error"] == pytest.approx(0.0)
    assert scores.loc["persistence", "day_error"] == pytest.approx(0.3)
    assert scores.loc["exact", "day_skill"] == pytest.approx(1.0)
    assert scores.loc["persistence", "day_skill"] == pytest.approx(0.0)


def _matched_log(days=12, seed=0):
    """Two models over `days` fully resolved days: one whose median is
    the truth plus noise, and persistence, whose median is further off."""
    rng = np.random.default_rng(seed)
    rows = []
    for day in range(days):
        origin = pd.Timestamp("2026-01-01 10:00", tz="UTC") + pd.Timedelta(days=day)
        truth = rng.normal(-1, 0.3, 24)
        for model, spread in (("good", 0.1), ("persistence", 0.4)):
            q50 = truth + rng.normal(0, spread, 24)
            for hour in range(24):
                rows.append({"origin": origin,
                             "target_time": origin + pd.Timedelta(hours=hour + 1),
                             "horizon": hour + 1, "model": model,
                             "q05": q50[hour] - 0.6, "q25": q50[hour] - 0.25,
                             "q50": q50[hour], "q75": q50[hour] + 0.25,
                             "q95": q50[hour] + 0.6, "y_true": truth[hour]})
    return pd.DataFrame(rows)


def test_matched_skill_brackets_its_point_and_beats_persistence():
    matched = daily_run.matched_skill(_matched_log(), "good")
    assert matched is not None
    assert matched["days"] == 12
    for key in ("hourly", "day"):
        point, low, high = matched[key]
        assert low <= point <= high
        assert point > 0
    assert daily_run.matched_skill(_matched_log(days=5), "good") is None


def test_timing_lines_state_exceptions_and_never_assume_an_audit():
    assert not any("Every row" in line for line in daily_run.timing_lines(None))
    clean = " ".join(daily_run.timing_lines([]))
    assert "Every row from an earlier run was committed" in clean
    assert "no exceptions so far" in clean and "listed below" not in clean
    late = [{"origin": pd.Timestamp("2026-09-03 10:00", tz="UTC"), "models": 8,
             "committed": pd.Timestamp("2026-09-04 05:15", tz="UTC"),
             "minutes_late": 1035.0, "sha": "c9feb5305"}]
    text = " ".join(daily_run.timing_lines(late))
    assert "Any exceptions and their reasons are listed below" in text
    assert "completed. The machine that ran the daily job" in text
    assert "hour starting 10:00 UTC (8 models)" in text and "17 hours" in text
    short = [dict(late[0], minutes_late=20.0)]
    assert "20 minutes after" in " ".join(daily_run.timing_lines(short))
    # a later day with no recorded reason takes it from the commit subject
    later = [dict(late[0], origin=pd.Timestamp("2026-09-28 10:00", tz="UTC"),
                  subject="Daily run 2026-09-28: 192 forecast rows logged; "
                          "trigger workflow_dispatch, started 12:30 UTC")]
    text = " ".join(daily_run.timing_lines(later))
    assert "started by a dispatch from the author's machine at 12:30 UTC" in text
    unknown = [dict(later[0], subject="Daily run 2026-09-28: 192 rows")]
    assert "No reason is recorded" in " ".join(daily_run.timing_lines(unknown))


def test_fixed_origin_is_the_same_clock_hour_whenever_the_run_starts():
    idx = pd.date_range("2026-09-26 00:00", "2026-09-27 15:00", freq="h",
                        tz="UTC")
    hourly = pd.DataFrame({"log_rv": 0.0}, index=idx)
    ten = pd.Timestamp("2026-09-27 10:00", tz="UTC")
    for start in ("2026-09-27 11:15", "2026-09-27 15:38", "2026-09-27 23:59"):
        assert daily_run.fixed_origin(hourly, pd.Timestamp(start, tz="UTC")) == ten
    # before the 10:00 hour has closed there is nothing to forecast
    with pytest.raises(ValueError, match="has not closed"):
        daily_run.fixed_origin(hourly, pd.Timestamp("2026-09-27 10:59", tz="UTC"))
    # a missing value at the origin hour is a visible failure, not a substitute
    hourly.loc[ten, "log_rv"] = float("nan")
    with pytest.raises(ValueError):
        daily_run.fixed_origin(hourly, pd.Timestamp("2026-09-27 11:15", tz="UTC"))


def test_live_report_written(logs_in_tmp):
    hourly = _frame()
    feats = build_features(hourly)
    daily_run.log_forecasts(feats, hourly.index[-25])
    daily_run.score_due(hourly)
    path = daily_run.write_live_report()
    text = path.read_text()
    assert "persistence" in text and "pinball" in text
    # one scored day -> the calibration check must stay inactive, not report a result
    assert "calibration check stays inactive" in text
    assert "day_error" in text and (logs_in_tmp / "figures" / "fig_live_daily.png").exists()


def _ev(cov_by_model, start="2026-01-01"):
    """Synthetic evaluation log. cov_by_model maps a model to its list of
    per-day coverage fractions; each day is 24 hourly rows and the first
    round(24 * frac) of them are placed inside the band."""
    rows = []
    for model, fracs in cov_by_model.items():
        for day, frac in enumerate(fracs):
            origin = pd.Timestamp(start, tz="UTC") + pd.Timedelta(days=day)
            inside = round(24 * frac)
            for hour in range(24):
                rows.append({
                    "origin": origin, "horizon": hour + 1,
                    "target_time": origin + pd.Timedelta(hours=hour + 1),
                    "model": model, "q05": 0.0, "q25": 0.0, "q50": 0.5,
                    "q75": 1.0, "q95": 1.0,
                    "y_true": 0.5 if hour < inside else 5.0,
                })
    return pd.DataFrame(rows)


def _lines(cov_by_model):
    evaluations = _ev(cov_by_model)
    return daily_run.calibration_lines(evaluations, evaluations["origin"].dt.date.nunique())


def test_calibration_gated_below_min_days():
    lines = _lines({"a": [1.0] * 3})
    assert "inactive" in lines[0]
    assert "3 so far" in lines[0]


def test_calibration_passes_when_coverage_is_at_target():
    # jitter around 0.90 so the day-level spread is real but centered
    cov = [0.875, 0.917, 0.875, 0.917, 0.958, 0.833, 0.917, 0.875,
           0.958, 0.875, 0.917, 0.833, 0.875, 0.917]
    lines = _lines({"a": cov})
    assert "passes" in lines[0]
    assert "Bonferroni correction" in lines[0]
    assert "0.05 divided by 1, or 0.0500" in lines[0]


def test_calibration_flags_a_persistently_miscalibrated_model():
    # far enough below target that the corrected test rejects on each of
    # the last three days, not just the latest one
    lines = _lines({"a": [0.500, 0.542, 0.458, 0.500, 0.583, 0.458, 0.500,
                          0.542, 0.500, 0.458, 0.542, 0.500, 0.583, 0.500]})
    assert "flags" in lines[0]
    assert "a, coverage 0.5" in lines[0]


def test_rejection_short_of_the_streak_is_not_reported():
    """The regression this change exists for. This model rejects the
    corrected test today and again on the window ending yesterday, but
    not the day before that, so it is reported as pending rather than
    flagged."""
    cov = [0.875, 0.875, 0.917, 0.792, 0.750, 0.917,
           0.917, 0.917, 0.833, 0.792, 0.792, 0.708]
    evaluations = _ev({"a": cov})
    assert daily_run.coverage_test_results(evaluations)["a"]["reject"]
    assert daily_run.rejection_streaks(evaluations) == {"a": 2}
    lines = daily_run.calibration_lines(evaluations,
                                        evaluations["origin"].dt.date.nunique())
    assert "passes" in lines[0]
    assert "day 2 of 3" in lines[0]


def test_no_result_when_daily_coverage_has_no_spread():
    """Zero spread leaves the test no uncertainty to divide by, so the
    model gets no result rather than an invented one."""
    evaluations = _ev({"a": [1.0] * 14})
    assert daily_run.coverage_test_results(evaluations) == {}


def test_correction_is_applied_across_models_tested():
    cov = [0.917, 0.875, 0.917, 0.875, 0.958, 0.875, 0.917,
           0.875, 0.917, 0.958, 0.875, 0.917, 0.875, 0.917]
    one = daily_run.coverage_test_results(_ev({"a": cov}))
    four = daily_run.coverage_test_results(
        _ev({"a": cov, "b": cov, "c": cov, "d": cov}))
    assert one["a"]["alpha"] == pytest.approx(0.05)
    assert four["a"]["alpha"] == pytest.approx(0.05 / 4)


def test_models_below_min_days_are_not_tested():
    cov = [0.917, 0.875, 0.917, 0.875, 0.958, 0.875, 0.917,
           0.875, 0.917, 0.958, 0.875, 0.917, 0.875, 0.917]
    results = daily_run.coverage_test_results(_ev({"a": cov, "young": cov[:5]}))
    assert "a" in results and "young" not in results
