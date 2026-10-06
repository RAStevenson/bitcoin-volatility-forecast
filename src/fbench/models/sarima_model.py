"""The SARIMAX model, a seasonal state space ARMA on log RV with a
24-hour seasonal period."""

from typing import cast

from scipy.stats import norm
from statsmodels.tsa.statespace.sarimax import SARIMAX, SARIMAXResults

from fbench.harness_config import QUANTILES, SARIMA_TRAIN_DAYS
from fbench.models.base_forecast_model import BaseForecastModel, quantile_frame, register


@register
class Sarima(BaseForecastModel):
    """SARIMAX(1,0,1)(1,0,1,24) on log RV. Log RV is roughly stationary,
    so d=D=0; the 24-hour seasonal terms carry the diurnal cycle. Train
    window is short because fit cost grows quickly with series length."""
    name = "sarima"
    train_days = SARIMA_TRAIN_DAYS

    def fit(self, train):
        """Fits the SARIMAX state space model on the training window
        and stores the fitted result on the instance. Fitting is
        capped at 200 iterations, so a window that has not converged
        still returns rather than stalling the daily run."""
        # Keep the regular hourly index (SARIMAX's Kalman filter handles
        # NaN observations natively); asfreq re-attaches the frequency
        # that .loc slicing drops, so forecasts carry real timestamps.
        y = train["log_rv"].asfreq("h")
        self.res_ = cast(SARIMAXResults,
                         SARIMAX(y, order=(1, 0, 1),
                                 seasonal_order=(1, 0, 1, 24),
                                 trend="c").fit(disp=False, maxiter=200))

    def predict(self, index):
        """Returns the five quantile columns built from the forecast
        mean and its standard error under a normal law, so the bands
        are symmetric in log RV and widen with the horizon."""
        forecast = self.res_.get_forecast(len(index))
        mean = forecast.predicted_mean.to_numpy()
        standard_error = forecast.se_mean.to_numpy()
        normal_quantiles = norm.ppf(QUANTILES)
        bands = mean[:, None] + standard_error[:, None] * normal_quantiles[None, :]
        return quantile_frame(bands, index)
