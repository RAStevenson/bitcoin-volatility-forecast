import numpy as np

from fbench.config import HORIZON, QUANTILES
from fbench.models.base import ForecastModel, quantile_frame, register


@register
class Persistence(ForecastModel):
    """Forecast = last observed log RV. Quantiles from the empirical
    distribution of per-horizon changes over the train window."""
    name = "persistence"

    def fit(self, train):
        y = train["log_rv"]
        self.last_ = y.dropna().iloc[-1]
        self.res_q_ = {}
        for h in range(1, HORIZON + 1):
            e = (y.shift(-h) - y).dropna()
            self.res_q_[h] = np.quantile(e, QUANTILES)

    def predict(self, index):
        rows = [self.last_ + self.res_q_[h]
                for h in range(1, len(index) + 1)]
        return quantile_frame(rows, index)


@register
class SeasonalPersistence(ForecastModel):
    """Forecast = log RV at the same hour one day earlier. The day-ahead
    seasonal naive; the honest floor for a seasonal series."""
    name = "seasonal_persistence"

    def fit(self, train):
        y = train["log_rv"]
        self.tail_ = y.iloc[-HORIZON:]          # the last 24 observed hours
        e = (y - y.shift(HORIZON)).dropna()     # day-over-day change
        self.res_q_ = np.quantile(e, QUANTILES)

    def predict(self, index):
        base = self.tail_.to_numpy()[:len(index)]
        rows = [b + self.res_q_ for b in base]
        return quantile_frame(rows, index)
