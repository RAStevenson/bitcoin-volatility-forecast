"""The Prophet entrant, additive trend plus Fourier seasonality fit on
log RV."""

import numpy as np
import pandas as pd
from prophet import Prophet

from fbench.harness_config import QUANTILES
from src.fbench.models.base_forecast_model import BaseForecastModel, quantile_frame, register


@register
class ProphetModel(BaseForecastModel):
    """Prophet on log RV with daily+weekly Fourier seasonality. Quantiles
    from predictive_samples rather than the fixed-width interval API, so we
    get all five quantiles from one fit."""
    name = "prophet"

    def fit(self, train):
        """Fits Prophet on the non-missing log RV rows with daily and
        weekly seasonality, no yearly term, and 300 uncertainty draws
        retained for predict."""
        df = train["log_rv"].dropna().reset_index()
        df.columns = ["ds", "y"]
        df["ds"] = df["ds"].dt.tz_localize(None)  # Prophet requires naive
        self.m_ = Prophet(daily_seasonality=True, weekly_seasonality=True,
                          yearly_seasonality=False, uncertainty_samples=300)
        self.m_.fit(df)

    def predict(self, index):
        """Draws predictive samples at the target timestamps and returns
        their empirical quantiles, so the band comes from the sample
        spread rather than Prophet's fixed-width interval API."""
        future = pd.DataFrame({"ds": index.tz_localize(None)})
        samples = self.m_.predictive_samples(future)["yhat"]
        qs = np.quantile(samples, QUANTILES, axis=1).T
        return quantile_frame(qs, index)
