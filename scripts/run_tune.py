"""Score candidate settings for the tuned models by grid search over
origins that all fall before the pinned backtest's test year, and write
one json per model under results/tuning/ with every candidate's mean
pinball loss, error, coverage and fit time. Each candidate is the model
class with other settings, run through the same engine as the backtest
at the daily run's origin hour. The script scores and records; adopting
a winner is a separate edit to the model's settings."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import argparse
import itertools
import json
import time

import pandas as pd

import bitcoin_volatility_forecast.models.persistence_model  # noqa: F401  (the reference row)
from bitcoin_volatility_forecast.data.hourly_series import load_hourly
from bitcoin_volatility_forecast.feature_builder import build_features
from bitcoin_volatility_forecast.forecast_settings import (
    HISTORY_START,
    ORIGIN_HOUR_UTC,
    RESULTS_DIR,
    SARIMA_TRAIN_DAYS,
    TRAIN_DAYS,
)
from bitcoin_volatility_forecast.models.nhits_model import NHits
from bitcoin_volatility_forecast.models.prophet_model import ProphetModel
from bitcoin_volatility_forecast.models.sarima_model import Sarima
from bitcoin_volatility_forecast.models.xgboost_model import XGBOOST_PARAMS, Gbm
from bitcoin_volatility_forecast.quantile_scoring import score
from bitcoin_volatility_forecast.rolling_backtest import make_origins, run_backtest

# The first origin day of the pinned backtest's test year
# (results/backtest/backtest_20260805.json: 365 days to 2026-08-05).
# Tuning sees no hour from this day on, so its data never overlaps the
# year the backtest scores.
TEST_YEAR_START = "2025-08-05"

# Eight candidates per tuned model, each a complete grid, the current
# setting among them. SARIMAX is respecified rather than tuned: four
# forms chosen once, plus the sine-cosine form on the long window since
# that form is cheap enough to afford it.
GBM_GRID = {
    f"depth{depth}_rate{rate}_sample{sample}": {
        "params": {**XGBOOST_PARAMS, "max_depth": depth, "learning_rate": rate,
                   "subsample": sample, "colsample_bytree": sample}}
    for depth, rate, sample in itertools.product((4, 6), (0.05, 0.10), (0.8, 1.0))}
NHITS_GRID = {
    f"width{width}_epochs{epochs}_rate{rate}": {
        "hidden_size": width, "max_epochs": epochs, "learning_rate": rate}
    for width, epochs, rate in itertools.product((64, 128), (3, 8), (1e-3, 3e-3))}
PROPHET_GRID = {
    f"changepoint{changepoint}_seasonality{seasonality}": {
        "changepoint_prior_scale": changepoint, "seasonality_prior_scale": seasonality}
    for changepoint, seasonality in itertools.product((0.01, 0.05, 0.2, 0.5), (1.0, 10.0))}
SARIMA_CANDIDATES = {
    "seasonal_arma_90d": {"order": (1, 0, 1), "seasonal_order": (1, 0, 1, 24),
                          "fourier_harmonics": 0, "train_days": SARIMA_TRAIN_DAYS},
    "seasonal_arma_365d": {"order": (1, 0, 1), "seasonal_order": (1, 0, 1, 24),
                           "fourier_harmonics": 0, "train_days": TRAIN_DAYS},
    "seasonal_ar_only_90d": {"order": (1, 0, 1), "seasonal_order": (1, 0, 0, 24),
                             "fourier_harmonics": 0, "train_days": SARIMA_TRAIN_DAYS},
    "fourier2_90d": {"order": (1, 0, 1), "seasonal_order": (0, 0, 0, 0),
                     "fourier_harmonics": 2, "train_days": SARIMA_TRAIN_DAYS},
    "fourier2_365d": {"order": (1, 0, 1), "seasonal_order": (0, 0, 0, 0),
                      "fourier_harmonics": 2, "train_days": TRAIN_DAYS},
}
GRIDS = {"gbm": (Gbm, GBM_GRID), "nhits": (NHits, NHITS_GRID),
         "prophet": (ProphetModel, PROPHET_GRID), "sarima": (Sarima, SARIMA_CANDIDATES)}


def tuning_origins(features, stride_days, origin_hour_utc):
    """Every origin from the first one with a full training window after
    HISTORY_START to the last whose 24 targets end before TEST_YEAR_START,
    one every stride_days, at origin_hour_utc. The features frame handed
    in must already stop before TEST_YEAR_START."""
    first_usable = (pd.Timestamp(HISTORY_START, tz="UTC") + pd.Timedelta(days=TRAIN_DAYS)
                    + pd.Timedelta(hours=origin_hour_utc))
    last_origin = make_origins(features.index, 1, 1, origin_hour_utc)[-1]
    span_days = (last_origin - first_usable).days + 1
    return make_origins(features.index, span_days, stride_days, origin_hour_utc)


def tuning_data(hourly):
    """The hours the tuning may see, every hour before TEST_YEAR_START,
    so nothing from the year the backtest scores reaches a candidate's
    fit or its score."""
    return hourly[hourly.index < pd.Timestamp(TEST_YEAR_START, tz="UTC")]


def check_before_test_year(origins):
    """Raise ValueError unless every origin's 24 target hours end before
    TEST_YEAR_START."""
    test_year_start = pd.Timestamp(TEST_YEAR_START, tz="UTC")
    if origins[-1] + pd.Timedelta(hours=24) >= test_year_start:
        raise ValueError(f"the last tuning origin {origins[-1]} has target hours "
                         f"in the test year, which starts {test_year_start}")


def summarize(forecasts):
    """The horizon-averaged scorecard of one candidate's forecasts, as a
    plain dict of floats."""
    scorecard = score(forecasts)
    return {column: float(scorecard[column].mean())
            for column in ("pinball_mean", "mae", "cov50", "cov90")}


def json_ready(settings):
    """Settings with tuples turned into lists so json can write them."""
    return {key: list(value) if isinstance(value, tuple) else value
            for key, value in settings.items()}


def main():
    """Scores every candidate of every requested model on the tuning
    origins and writes results/tuning/tune_<model>_<date>.json after each
    candidate, so a stopped run keeps what it scored."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", default=",".join(GRIDS),
                        help="comma-separated subset of " + ", ".join(GRIDS))
    parser.add_argument("--stride", type=int, default=5,
                        help="days between origins; 5 cycles the weekday")
    parser.add_argument("--origin-hour", type=int, default=ORIGIN_HOUR_UTC)
    parser.add_argument("--candidates", default=None,
                        help="comma-separated candidate labels to score, "
                             "for a trial run; default every candidate")
    args = parser.parse_args()

    tuning_hours = tuning_data(load_hourly())
    features = build_features(tuning_hours)
    origins = tuning_origins(features, args.stride, args.origin_hour)
    check_before_test_year(origins)
    print(f"tuning origins: {len(origins)} from {origins[0]} to {origins[-1]}, "
          f"data to {tuning_hours.index[-1]}", flush=True)

    reference = summarize(run_backtest(features, ["persistence"], origins))
    print(f"persistence on these origins: pinball {reference['pinball_mean']:.4f}",
          flush=True)
    out_dir = RESULTS_DIR / "tuning"
    out_dir.mkdir(parents=True, exist_ok=True)
    date_stamp = pd.Timestamp.now(tz="UTC").strftime("%Y%m%d")

    for model_name in args.models.split(","):
        base_class, grid = GRIDS[model_name]
        labels = args.candidates.split(",") if args.candidates else list(grid)
        record = {"model": model_name, "origin_hour_utc": args.origin_hour,
                  "stride": args.stride, "origins": len(origins),
                  "first_origin": str(origins[0]), "last_origin": str(origins[-1]),
                  "data_end": str(tuning_hours.index[-1]),
                  "test_year_start": TEST_YEAR_START,
                  "persistence": reference, "candidates": []}
        out_path = out_dir / f"tune_{model_name}_{date_stamp}.json"
        for label in labels:
            settings = grid[label]
            candidate_class = type(f"{base_class.__name__}Candidate", (base_class,),
                                   {"name": label, **settings})
            started = time.perf_counter()
            forecasts = run_backtest(features, [label], origins,
                                     registry={label: candidate_class})
            seconds = time.perf_counter() - started
            result = {"label": label, "settings": json_ready(settings),
                      **summarize(forecasts),
                      "seconds_per_origin": seconds / len(origins)}
            record["candidates"].append(result)
            out_path.write_text(json.dumps(record, indent=1))
            print(f"{model_name} {label}: pinball {result['pinball_mean']:.4f} "
                  f"mae {result['mae']:.4f} cov90 {result['cov90']:.3f} "
                  f"{result['seconds_per_origin']:.1f}s/origin", flush=True)
        ranked = sorted(record["candidates"], key=lambda row: row["pinball_mean"])
        print(f"{model_name} best: {ranked[0]['label']} "
              f"(pinball {ranked[0]['pinball_mean']:.4f}) -> {out_path.name}", flush=True)


if __name__ == "__main__":
    main()
