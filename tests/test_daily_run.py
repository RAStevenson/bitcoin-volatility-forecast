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
    timestamps = pd.date_range("2025-01-01", periods=n_hours, freq="h", tz="UTC")
    random_generator = np.random.default_rng(seed)
    log_realized_vol = (pd.Series(random_generator.normal(0, 0.3, n_hours),
                                  index=timestamps)
                        .rolling(3).mean())
    return pd.DataFrame({"log_rv": log_realized_vol, "rv": np.exp(log_realized_vol)},
                        index=timestamps)


def test_log_forecasts_is_idempotent_per_origin(logs_in_tmp):
    hourly = _frame()
    features = build_features(hourly)
    origin = hourly.index[-30]  # leave future hours unobserved
    rows_first_run = daily_run.log_forecasts(features, origin)
    assert rows_first_run > 0
    rows_second_run = daily_run.log_forecasts(features, origin)
    assert rows_second_run == 0


def test_score_due_resolves_only_observed_hours(logs_in_tmp):
    hourly = _frame()
    features = build_features(hourly)
    origin = hourly.index[-13]  # only 12 of 24 target hours observed
    daily_run.log_forecasts(features, origin)
    n_models = len(pd.read_csv(daily_run.FORECAST_LOG)["model"].unique())
    resolved = daily_run.score_due(hourly)
    assert resolved == 12 * n_models
    assert daily_run.score_due(hourly) == 0  # second pass appends nothing


def test_score_due_waits_for_the_hour_to_end(logs_in_tmp):
    hourly = _frame()
    features = build_features(hourly)
    origin = hourly.index[-30]
    daily_run.log_forecasts(features, origin)
    n_models = len(pd.read_csv(daily_run.FORECAST_LOG)["model"].unique())
    # every target hour has an actual, but only the hours that have ENDED
    # by the clock may resolve: targets origin+1h .. origin+12h end by
    # origin+13h, the 13th is still in progress
    resolved = daily_run.score_due(hourly, now=origin + pd.Timedelta(hours=13))
    assert resolved == 12 * n_models


def test_logs_are_appended_not_rewritten(logs_in_tmp):
    hourly = _frame()
    features = build_features(hourly)
    daily_run.log_forecasts(features, hourly.index[-60])
    bytes_after_first = daily_run.FORECAST_LOG.read_bytes()
    daily_run.log_forecasts(features, hourly.index[-30])
    bytes_after_second = daily_run.FORECAST_LOG.read_bytes()
    assert bytes_after_second.startswith(bytes_after_first)  # earlier bytes untouched
    assert bytes_after_second.count(b"\n") > bytes_after_first.count(b"\n")


def test_expected_vol_raises_the_median_by_the_band_spread():
    # a band with no spread is its own middle
    assert daily_run.expected_vol({"q25": [0.0], "q50": [0.0], "q75": [0.0]})[0] == 1.0
    # a 25-75 band one sigma wide on the log scale raises the middle by exp(1/2)
    sigma = daily_run.IQR_TO_SIGMA
    raised = daily_run.expected_vol({"q25": [-sigma / 2], "q50": [0.0], "q75": [sigma / 2]})
    assert raised[0] == pytest.approx(np.exp(0.5))
    # the correction is the same whatever the median
    shifted = daily_run.expected_vol({"q25": [1 - sigma / 2], "q50": [1.0],
                                      "q75": [1 + sigma / 2]})
    assert shifted[0] == pytest.approx(np.exp(1.5))


def test_day_level_scores_reward_the_right_day_average():
    """The day score averages each hour's expected volatility, so a model
    whose medians sit exactly one band correction under the truth scores
    a zero day error, and one 0.3 above that scores 0.3."""
    target_times = pd.date_range("2026-01-01 01:00", periods=48, freq="h", tz="UTC")
    origins = [target_times[0] - pd.Timedelta(hours=1),
               target_times[24] - pd.Timedelta(hours=1)]
    correction = (1.0 / daily_run.IQR_TO_SIGMA) ** 2 / 2  # for a 25-75 band 1.0 wide
    rows = []
    for origin, day_targets in zip(origins, (target_times[:24], target_times[24:]),
                                   strict=True):
        truth = np.linspace(-1.2, -0.8, 24)
        for model, offset in (("exact", 0.0), ("persistence", 0.3)):
            for i, target_time in enumerate(day_targets):
                median = truth[i] - correction + offset
                rows.append({"origin": origin, "target_time": target_time,
                             "horizon": i + 1, "model": model,
                             "q05": median - 1, "q25": median - .5,
                             "q50": median, "q75": median + .5,
                             "q95": median + 1, "y_true": truth[i]})
    scores = daily_run.day_level_scores(pd.DataFrame(rows))
    assert scores.loc["exact", "day_error"] == pytest.approx(0.0)
    assert scores.loc["persistence", "day_error"] == pytest.approx(0.3)
    assert scores.loc["exact", "day_skill"] == pytest.approx(1.0)
    assert scores.loc["persistence", "day_skill"] == pytest.approx(0.0)


def _matched_log(days=12, seed=0):
    """Two models over `days` fully resolved days: one whose median is
    the truth plus noise, and persistence, whose median is further off."""
    random_generator = np.random.default_rng(seed)
    rows = []
    for day in range(days):
        origin = pd.Timestamp("2026-01-01 10:00", tz="UTC") + pd.Timedelta(days=day)
        truth = random_generator.normal(-1, 0.3, 24)
        for model, spread in (("good", 0.1), ("persistence", 0.4)):
            median_forecast = truth + random_generator.normal(0, spread, 24)
            for hour in range(24):
                rows.append({"origin": origin,
                             "target_time": origin + pd.Timedelta(hours=hour + 1),
                             "horizon": hour + 1, "model": model,
                             "q05": median_forecast[hour] - 0.6,
                             "q25": median_forecast[hour] - 0.25,
                             "q50": median_forecast[hour],
                             "q75": median_forecast[hour] + 0.25,
                             "q95": median_forecast[hour] + 0.6, "y_true": truth[hour]})
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
    clean_text = " ".join(daily_run.timing_lines([]))
    assert "Every row from an earlier run was committed" in clean_text
    assert "no exceptions so far" in clean_text and "listed below" not in clean_text
    late = [{"origin": pd.Timestamp("2026-09-03 10:00", tz="UTC"), "models": 8,
             "committed": pd.Timestamp("2026-09-04 05:15", tz="UTC"),
             "minutes_late": 1035.0, "sha": "c9feb5305"}]
    text = " ".join(daily_run.timing_lines(late))
    assert "completed, except on the days listed below" in text
    assert "completed. The machine that ran the daily job" in text
    assert "hour starting 10:00 UTC (8 models)" in text and "17 hours" in text
    short_delay = [dict(late[0], minutes_late=20.0)]
    assert "20 minutes after" in " ".join(daily_run.timing_lines(short_delay))
    # a later day with no recorded reason takes it from the commit subject
    later = [dict(late[0], origin=pd.Timestamp("2026-09-28 10:00", tz="UTC"),
                  subject="Daily run 2026-09-28: 192 forecast rows logged; "
                          "trigger workflow_dispatch, started 12:30 UTC")]
    text = " ".join(daily_run.timing_lines(later))
    assert "started by a dispatch from the author's machine at 12:30 UTC" in text
    unknown = [dict(later[0], subject="Daily run 2026-09-28: 192 rows")]
    assert "No reason is recorded" in " ".join(daily_run.timing_lines(unknown))


def test_fixed_origin_is_the_same_clock_hour_whenever_the_run_starts():
    timestamps = pd.date_range("2026-09-26 00:00", "2026-09-27 15:00", freq="h",
                               tz="UTC")
    hourly = pd.DataFrame({"log_rv": 0.0}, index=timestamps)
    ten_utc = pd.Timestamp("2026-09-27 10:00", tz="UTC")
    for start in ("2026-09-27 11:15", "2026-09-27 15:38", "2026-09-27 23:59"):
        assert daily_run.fixed_origin(hourly, pd.Timestamp(start, tz="UTC")) == ten_utc
    # before the 10:00 hour has closed there is nothing to forecast
    with pytest.raises(ValueError, match="has not closed"):
        daily_run.fixed_origin(hourly, pd.Timestamp("2026-09-27 10:59", tz="UTC"))
    # a missing value at the origin hour is a visible failure, not a substitute
    hourly.loc[ten_utc, "log_rv"] = float("nan")
    with pytest.raises(ValueError):
        daily_run.fixed_origin(hourly, pd.Timestamp("2026-09-27 11:15", tz="UTC"))


def test_live_report_written(logs_in_tmp):
    hourly = _frame()
    features = build_features(hourly)
    daily_run.log_forecasts(features, hourly.index[-25])
    daily_run.score_due(hourly)
    path = daily_run.write_live_report()
    text = path.read_text()
    assert "persistence" in text and "pinball" in text
    # the coverage columns are glossed
    assert "for well-sized bands they sit near 0.50 and 0.90" in text
    assert "day_error" in text and (logs_in_tmp / "figures" / "fig_live_daily.png").exists()
    # the settings sentence: this synthetic record sits before the release origin
    assert "model settings" in text


def test_settings_lines_say_which_settings_the_days_ran_on(monkeypatch):
    monkeypatch.setattr(daily_run, "RELEASE_ORIGIN", "2026-03-01 10:00")
    rows = []
    for day in range(6):
        origin = pd.Timestamp("2026-02-26 10:00", tz="UTC") + pd.Timedelta(days=day)
        for model, spread in (("good", 0.1), ("persistence", 0.4)):
            for hour in range(24):
                rows.append({"origin": origin,
                             "target_time": origin + pd.Timedelta(hours=hour + 1),
                             "horizon": hour + 1, "model": model,
                             "q05": -1.6, "q25": -1.25, "q50": -1.0 + spread,
                             "q75": -0.75, "q95": -0.4, "y_true": -1.0})
    evaluations = pd.DataFrame(rows)
    blended = " ".join(daily_run.settings_lines(evaluations))
    assert "changed on 2026-03-01" in blended and "On the 3 forecast days" in blended
    assert "good leads" in blended
    before_only = evaluations[evaluations["origin"] < pd.Timestamp("2026-03-01", tz="UTC")]
    assert "has resolved yet" in " ".join(daily_run.settings_lines(before_only))
    after_only = evaluations[evaluations["origin"] >= pd.Timestamp("2026-03-01", tz="UTC")]
    assert "in force since 2026-03-01" in " ".join(daily_run.settings_lines(after_only))
