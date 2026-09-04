"""The SARIMAX entrant, a seasonal state space ARMA on log RV with a
24-hour seasonal period."""

from scipy.stats import norm
from statsmodels.tsa.statespace.sarimax import SARIMAX

from fbench.harness_config import QUANTILES, SARIMA_TRAIN_DAYS
from fbench.models.forecast_model import ForecastModel, quantile_frame, register


@register
class Sarima(ForecastModel):
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
        self.res_ = SARIMAX(y, order=(1, 0, 1),
                            seasonal_order=(1, 0, 1, 24),
                            trend="c").fit(disp=False, maxiter=200)

    def predict(self, index):
        """Returns the five quantile columns built from the forecast
        mean and its standard error under a normal law, so the bands
        are symmetric in log RV and widen with the horizon."""
        fc = self.res_.get_forecast(len(index))
        mean = fc.predicted_mean.to_numpy()
        se = fc.se_mean.to_numpy()
        z = norm.ppf(QUANTILES)
        return quantile_frame(mean[:, None] + se[:, None] * z[None, :],
                              index)
