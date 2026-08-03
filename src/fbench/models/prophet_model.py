import numpy as np
import pandas as pd
from prophet import Prophet

from fbench.config import QUANTILES
from fbench.models.base import ForecastModel, quantile_frame, register


@register
class ProphetModel(ForecastModel):
    """Prophet on log RV with daily+weekly Fourier seasonality. Quantiles
    from predictive_samples rather than the fixed-width interval API, so we
    get all five quantiles from one fit."""
    name = "prophet"

    def fit(self, train):
        df = train["log_rv"].dropna().reset_index()
        df.columns = ["ds", "y"]
        df["ds"] = df["ds"].dt.tz_localize(None)  # Prophet requires naive
        self.m_ = Prophet(daily_seasonality=True, weekly_seasonality=True,
                          yearly_seasonality=False, uncertainty_samples=300)
        self.m_.fit(df)

    def predict(self, index):
        future = pd.DataFrame({"ds": index.tz_localize(None)})
        samples = self.m_.predictive_samples(future)["yhat"]
        qs = np.quantile(samples, QUANTILES, axis=1).T
        return quantile_frame(qs, index)
