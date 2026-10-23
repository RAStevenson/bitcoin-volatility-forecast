"""The SARIMAX model, a state space ARMA on log RV whose daily cycle is
carried either by 24-hour seasonal terms or by sine and cosine inputs
with a 24-hour period."""

from typing import ClassVar, cast

import numpy as np
import pandas as pd
from scipy.stats import norm
from statsmodels.tsa.statespace.sarimax import SARIMAX, SARIMAXResults

from bitcoin_volatility_forecast.forecast_settings import QUANTILES, SARIMA_TRAIN_DAYS
from bitcoin_volatility_forecast.models.base_forecast_model import (
    BaseForecastModel,
    quantile_frame,
    register,
)


def daily_cycle_terms(timestamps, harmonics):
    """Sine and cosine waves with a 24-hour period, harmonics pairs of
    them at one, two, ... cycles a day, on the timestamps' clock hour,
    as a frame indexed by the timestamps. These are the X inputs that
    give SARIMAX a fixed daily cycle in place of a seasonal ARMA."""
    hour = pd.DatetimeIndex(timestamps).hour.to_numpy()
    columns = {}
    for cycles_per_day in range(1, harmonics + 1):
        angle = 2 * np.pi * cycles_per_day * hour / 24
        columns[f"sin_{cycles_per_day}"] = np.sin(angle)
        columns[f"cos_{cycles_per_day}"] = np.cos(angle)
    return pd.DataFrame(columns, index=timestamps)


@register
class Sarima(BaseForecastModel):
    """SARIMAX on log RV. Log RV is roughly stationary, so no
    differencing; the daily cycle is carried by the seasonal_order terms
    with a 24-hour period, or, when fourier_harmonics is set, by that
    many sine and cosine pairs supplied as X inputs with no seasonal
    ARMA. The train window is short because fit cost grows quickly with
    series length. The class attributes are the settings; the tuning
    script scores candidates by subclassing with other values."""
    name = "sarima"
    train_days = SARIMA_TRAIN_DAYS
    order: ClassVar[tuple] = (1, 0, 1)
    seasonal_order: ClassVar[tuple] = (1, 0, 1, 24)
    fourier_harmonics = 0

    def fit(self, training_rows):
        """Fits the SARIMAX state space model on the training window
        and stores the fitted result on the instance. Fitting is
        capped at 200 iterations, so a window that has not converged
        still returns rather than stalling the daily run."""
        # Keep the regular hourly index (SARIMAX's Kalman filter handles
        # NaN observations natively); asfreq re-attaches the frequency
        # that .loc slicing drops, so forecasts carry real timestamps.
        y = training_rows["log_rv"].asfreq("h")
        exog = (daily_cycle_terms(y.index, self.fourier_harmonics)
                if self.fourier_harmonics else None)
        self.fitted_results_ = cast(SARIMAXResults,
                                    SARIMAX(y, exog=exog, order=self.order,
                                            seasonal_order=self.seasonal_order,
                                            trend="c").fit(disp=False, maxiter=200))

    def predict(self, target_times):
        """Returns the five quantile columns built from the forecast
        mean and its standard error under a normal law, so the bands
        are symmetric in log RV and widen with the horizon."""
        exog = (daily_cycle_terms(target_times, self.fourier_harmonics)
                if self.fourier_harmonics else None)
        forecast = self.fitted_results_.get_forecast(len(target_times), exog=exog)
        mean = forecast.predicted_mean.to_numpy()
        standard_error = forecast.se_mean.to_numpy()
        normal_quantiles = norm.ppf(QUANTILES)
        bands = mean[:, None] + standard_error[:, None] * normal_quantiles[None, :]
        return quantile_frame(bands, target_times)
