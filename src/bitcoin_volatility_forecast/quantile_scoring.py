"""Scoring for the backtest, computing pinball loss over the five
levels in QUANTILES together with point error, band coverage, and skill
against the persistence baseline. Every number here is computed on log
realized volatility, the space the models forecast in."""

import numpy as np
import pandas as pd

from bitcoin_volatility_forecast.forecast_settings import QCOLS, QUANTILES


def pinball(outcomes, quantile_forecast, quantile_level):
    """Mean pinball loss at quantile_level between outcomes and
    the forecasts in quantile_forecast, as a float where lower is better.
    The mean runs over every paired entry with no weighting, and the value
    carries the units of its inputs, which here is log realized
    volatility."""
    forecast_error = np.asarray(outcomes) - np.asarray(quantile_forecast)
    return float(np.mean(np.maximum(quantile_level * forecast_error,
                                    (quantile_level - 1) * forecast_error)))


def score(forecasts):
    """Scorecard indexed by (model, horizon), holding the pinball loss
    averaged over the five QUANTILES levels, the mean absolute and root
    mean squared error of the q50 forecast, the empirical coverage of the
    25-75 and 5-95 bands, and n, the rows scored. Rows with no outcome or
    a NaN quantile are dropped first, so n says how much of the frame
    each number rests on."""
    # Drop rows whose forecast itself is NaN (a degenerate fit) as well as
    # rows with no outcome yet; the per-group n makes the exclusion visible
    # rather than letting one bad fit erase a model's whole scorecard.
    rows = []
    for (model_name, horizon), group in forecasts.dropna(
            subset=["y_true", *QCOLS]).groupby(["model", "horizon"]):
        outcomes = group["y_true"].to_numpy()
        pinball_mean = np.mean([pinball(outcomes, group[column].to_numpy(), level)
                                for column, level in zip(QCOLS, QUANTILES, strict=True)])
        forecast_error = outcomes - group["q50"].to_numpy()
        rows.append({
            "model": model_name, "horizon": horizon, "pinball_mean": pinball_mean,
            "mae": float(np.mean(np.abs(forecast_error))),
            "rmse": float(np.sqrt(np.mean(forecast_error ** 2))),
            "cov50": float(np.mean((group["q25"] <= outcomes) & (outcomes <= group["q75"]))),
            "cov90": float(np.mean((group["q05"] <= outcomes) & (outcomes <= group["q95"]))),
            "n": len(group),
        })
    return pd.DataFrame(rows).set_index(["model", "horizon"]).sort_index()


def add_skill(scores):
    """Copy of the scorecard with a skill_vs_persistence column, one
    minus the model's pinball loss over the persistence model's pinball
    loss at the same horizon, so zero ties the baseline and positive
    beats it. The frame needs a persistence row at every horizon, and
    horizons it lacks come back as missing values."""
    persistence_pinball = scores.xs("persistence")["pinball_mean"]
    scores_with_skill = scores.copy()
    persistence_pinball_per_row = scores_with_skill.reset_index("model").join(
        persistence_pinball.rename("persistence_pinball"))["persistence_pinball"]
    scores_with_skill["skill_vs_persistence"] = (
        1 - scores_with_skill["pinball_mean"] / persistence_pinball_per_row.to_numpy())
    return scores_with_skill
