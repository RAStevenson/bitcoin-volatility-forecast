"""The two naive baselines the rest of the field has to beat, last
observed value and same hour one day earlier."""

import numpy as np

from fbench.harness_config import HORIZON, QUANTILES
from src.fbench.models.base_forecast_model import BaseForecastModel, quantile_frame, register


@register
class Persistence(BaseForecastModel):
    """Forecast = last observed log RV. Quantiles from the empirical
    distribution of per-horizon changes over the train window."""
    name = "persistence"

    def fit(self, train):
        """Records the last observed log RV and, for each horizon, the
        empirical quantiles of the h-step change across the training
        window."""
        y = train["log_rv"]
        self.last_ = y.dropna().iloc[-1]
        self.res_q_ = {}
        for h in range(1, HORIZON + 1):
            e = (y.shift(-h) - y).dropna()
            self.res_q_[h] = np.quantile(e, QUANTILES)

    def predict(self, index):
        """Returns the last observed value offset by each horizon's
        change quantiles, so the bands widen with horizon the same way
        the training changes did."""
        rows = [self.last_ + self.res_q_[h]
                for h in range(1, len(index) + 1)]
        return quantile_frame(rows, index)


@register
class SeasonalPersistence(BaseForecastModel):
    """Forecast = log RV at the same hour one day earlier. The day-ahead
    seasonal naive; the honest floor for a seasonal series."""
    name = "seasonal_persistence"

    def fit(self, train):
        """Keeps the last 24 observed hours as the point path and takes
        one set of quantiles from the day-over-day change, shared by
        every horizon rather than fitted per horizon."""
        y = train["log_rv"]
        self.tail_ = y.iloc[-HORIZON:]          # the last 24 observed hours
        e = (y - y.shift(HORIZON)).dropna()     # day-over-day change
        self.res_q_ = np.quantile(e, QUANTILES)

    def predict(self, index):
        """Returns yesterday's value at each target hour offset by the
        one set of day-over-day change quantiles, which leaves the band
        width flat across the horizon."""
        base = self.tail_.to_numpy()[:len(index)]
        rows = [b + self.res_q_ for b in base]
        return quantile_frame(rows, index)
