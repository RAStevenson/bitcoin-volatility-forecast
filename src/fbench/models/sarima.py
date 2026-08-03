from scipy.stats import norm
from statsmodels.tsa.statespace.sarimax import SARIMAX

from fbench.config import QUANTILES, SARIMA_TRAIN_DAYS
from fbench.models.base import ForecastModel, quantile_frame, register


@register
class Sarima(ForecastModel):
    """SARIMAX(1,0,1)(1,0,1,24) on log RV. Log RV is roughly stationary,
    so d=D=0; the 24-hour seasonal terms carry the diurnal cycle. Train
    window is short because fit cost grows quickly with series length."""
    name = "sarima"
    train_days = SARIMA_TRAIN_DAYS

    def fit(self, train):
        # Keep the regular hourly index (SARIMAX's Kalman filter handles
        # NaN observations natively); asfreq re-attaches the frequency
        # that .loc slicing drops, so forecasts carry real timestamps.
        y = train["log_rv"].asfreq("h")
        self.res_ = SARIMAX(y, order=(1, 0, 1),
                            seasonal_order=(1, 0, 1, 24),
                            trend="c").fit(disp=False, maxiter=200)

    def predict(self, index):
        fc = self.res_.get_forecast(len(index))
        mean = fc.predicted_mean.to_numpy()
        se = fc.se_mean.to_numpy()
        z = norm.ppf(QUANTILES)
        return quantile_frame(mean[:, None] + se[:, None] * z[None, :],
                              index)
