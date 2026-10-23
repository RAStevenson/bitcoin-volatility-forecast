"""The Prophet model, additive trend plus Fourier seasonality fit on
log RV."""

import numpy as np
import pandas as pd
from prophet import Prophet

from bitcoin_volatility_forecast.forecast_settings import QUANTILES
from bitcoin_volatility_forecast.models.base_forecast_model import (
    BaseForecastModel,
    quantile_frame,
    register,
)

SAMPLE_SEED = 7  # the same seed N-HiTS uses


@register
class ProphetModel(BaseForecastModel):
    """Prophet on log RV with daily+weekly Fourier seasonality. Quantiles
    from predictive_samples rather than the fixed-width interval API, so we
    get all five quantiles from one fit. The two class attributes are
    Prophet's flexibility settings: how freely the trend may change
    slope, and how large the seasonal cycles may be. The tuning script
    scores candidates by subclassing with other values."""
    name = "prophet"
    changepoint_prior_scale = 0.01
    seasonality_prior_scale = 10.0

    def fit(self, training_rows):
        """Fits Prophet on the non-missing log RV rows with daily and
        weekly seasonality, no yearly term, and 300 uncertainty draws
        retained for predict."""
        history = training_rows["log_rv"].dropna().reset_index()
        history.columns = ["ds", "y"]
        history["ds"] = history["ds"].dt.tz_localize(None)  # Prophet requires naive
        # Prophet ships no type hints; the checker reads its "auto" string
        # defaults as the parameter type, and its docstring accepts bools.
        self.prophet_ = Prophet(daily_seasonality=True,  # pyright: ignore[reportArgumentType]
                                weekly_seasonality=True,  # pyright: ignore[reportArgumentType]
                                yearly_seasonality=False,  # pyright: ignore[reportArgumentType]
                                changepoint_prior_scale=self.changepoint_prior_scale,
                                seasonality_prior_scale=self.seasonality_prior_scale,
                                uncertainty_samples=300)
        self.prophet_.fit(history)

    def predict(self, target_times):
        """Draws predictive samples at the target timestamps and returns
        their empirical quantiles, so the band comes from the sample
        spread rather than Prophet's fixed-width interval API."""
        future = pd.DataFrame({"ds": target_times.tz_localize(None)})
        # predictive_samples draws from numpy's global random generator
        # and takes no seed. Seed it here, and put the generator back
        # afterwards, so the band no longer depends on which model ran
        # before this one (until 2026-10-05 it was repeatable only
        # because N-HiTS, which runs first, seeds the generator).
        saved_random_state = np.random.get_state()
        np.random.seed(SAMPLE_SEED)
        try:
            samples = self.prophet_.predictive_samples(future)["yhat"]
        finally:
            np.random.set_state(saved_random_state)
        quantile_values = np.quantile(samples, QUANTILES, axis=1).T
        return quantile_frame(quantile_values, target_times)
