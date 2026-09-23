import numpy as np
import pandas as pd

import fbench.models.persistence_model  # noqa: F401  (registers baselines)
from fbench import daily_run, daily_forecast_generator, daily_forecast_scoring, review_generator
from fbench.feature_builder import build_features
from fbench.harness_config import HORIZON


def _hourly(n=24 * 400, seed=5, with_close=True):
    idx = pd.date_range("2025-01-01", periods=n, freq="h", tz="UTC")
    rng = np.random.default_rng(seed)
    lr = pd.Series(rng.normal(-1, 0.3, n), index=idx).rolling(3).mean()
    h = pd.DataFrame({"log_rv": lr, "rv": np.exp(lr)}, index=idx)
    if with_close:
        h["close"] = 100.0 * np.exp(rng.normal(0, 0.001, n).cumsum())
    return h


def test_claims_and_realized_agree_when_the_median_is_exact():
    h = _hourly()
    origin = h.index[-25]
    ctx = daily_forecast_generator.context(h["rv"].loc[:origin])
    tt = pd.date_range(origin + pd.Timedelta(hours=1), periods=HORIZON,
                       freq="h", tz="UTC")
    order = np.random.default_rng(1).permutation(HORIZON)
    med = np.linspace(0.3, 0.6, HORIZON)[order]
    vol = np.column_stack([med * 0.6, med * 0.8, med, med * 1.2, med * 1.6])
    c = daily_forecast_generator.claims(vol, tt, ctx)
    r = daily_forecast_generator.realized_claims(pd.Series(med, index=tt), ctx)
    assert c["regime"] == r["regime"]
    assert c["trend"] == r["trend"]
    assert set(c["loud"]) == set(r["loud"])
    assert set(c["calm"]) == set(r["calm"])
    assert c["regime"] in daily_forecast_generator.REGIMES


def _one_day_log(h, origin, end_price):
    """Evaluation log with one model over one origin, whose median
    forecast equals what realized, and a close series pinned at the two
    ends the day-move claim is measured between."""
    tt = pd.date_range(origin + pd.Timedelta(hours=1), periods=HORIZON,
                       freq="h", tz="UTC")
    y = h["log_rv"].reindex(tt).to_numpy()
    ev = pd.DataFrame({"origin": origin, "target_time": tt,
                       "horizon": range(1, HORIZON + 1),
                       "model": "persistence",
                       "q05": y - 0.5, "q25": y - 0.2, "q50": y,
                       "q75": y + 0.2, "q95": y + 0.5, "y_true": y})
    h = h.copy()
    h.loc[origin, "close"] = 100.0
    h.loc[origin + pd.Timedelta(hours=HORIZON), "close"] = end_price
    return ev, h


def test_day_move_hit_is_close_to_close():
    h = _hourly()
    origin = h.index[-25]
    ev, h_in = _one_day_log(h, origin, end_price=100.0)
    scored = daily_forecast_scoring.score_daily_forecast(ev, h_in)
    assert len(scored) == 1
    move = float(scored["day_move"].iloc[0])
    assert 0 < move < 0.2
    assert bool(scored["day_move_hit"].iloc[0]) is True
    # a day that moved twice the stated distance is a miss
    ev, h_out = _one_day_log(h, origin, end_price=100.0 * (1 + 2 * move))
    scored = daily_forecast_scoring.score_daily_forecast(ev, h_out)
    assert bool(scored["day_move_hit"].iloc[0]) is False
    # the exact-median day matches on every word and names every hour
    assert scored["regime_gap"].iloc[0] == 0
    assert scored["trend_fc"].iloc[0] == scored["trend_rz"].iloc[0]
    assert scored["loud_overlap"].iloc[0] == 3
    assert scored["calm_overlap"].iloc[0] == 3
    # the yesterday baseline is scored on the same day in the same terms
    for col in ("base_regime_hit", "base_trend_hit", "base_day_move_hit"):
        assert scored[col].iloc[0] in (True, False)
    assert 0 <= scored["base_loud_overlap"].iloc[0] <= 3
    assert scored["base_high_hours"].iloc[0] >= 0


def test_day_move_is_skipped_without_close():
    h = _hourly(with_close=False)
    origin = h.index[-25]
    ev, _ = _one_day_log(_hourly(), origin, end_price=100.0)
    scored = daily_forecast_scoring.score_daily_forecast(ev, h)
    assert scored["day_return"].iloc[0] is None
    lines = daily_forecast_scoring.record_lines(scored)
    assert not any("one-standard-deviation" in ln for ln in lines)
    assert any("regime word" in ln for ln in lines)
    assert any("Repeating yesterday's word" in ln for ln in lines)


def test_partially_resolved_day_is_not_scored():
    h = _hourly()
    origin = h.index[-25]
    ev, h_in = _one_day_log(h, origin, end_price=100.0)
    assert daily_forecast_scoring.score_daily_forecast(ev.iloc[:-1], h_in).empty


def test_review_carries_the_daily_forecast_record(tmp_path, monkeypatch):
    monkeypatch.setattr(daily_run, "FORECAST_LOG", tmp_path / "forecasts.csv")
    monkeypatch.setattr(daily_run, "EVAL_LOG", tmp_path / "evaluation.csv")
    monkeypatch.setattr(daily_run, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr(review_generator, "EVAL_LOG", daily_run.EVAL_LOG)
    monkeypatch.setattr(review_generator, "RESULTS_DIR", tmp_path)
    h = _hourly()
    origin = h.index[-25]
    daily_run.log_forecasts(build_features(h), origin)
    daily_run.score_due(h)
    text = review_generator.write_review(h).read_text()
    assert "The daily forecast's own claims" in text
    assert "Over 1 resolved days" in text
    assert "one-standard-deviation day move on" in text
    # without the hourly series the section is omitted, not faked
    assert "daily forecast's own claims" not in review_generator.build_review()
