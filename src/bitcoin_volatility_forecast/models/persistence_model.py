"""The two naive baselines the rest of the field has to beat, last
observed value and same hour one day earlier."""

import numpy as np

from bitcoin_volatility_forecast.forecast_settings import HORIZON, QUANTILES
from bitcoin_volatility_forecast.models.base_forecast_model import (
    BaseForecastModel,
    quantile_frame,
    register,
)


@register
class Persistence(BaseForecastModel):
    """Forecast = last observed log RV. Quantiles from the empirical
    distribution of per-horizon changes over the train window."""
    name = "persistence"

    def fit(self, training_rows):
        """Records the last observed log RV and, for each horizon, the
        empirical quantiles of the change over that many hours across the
        training window."""
        y = training_rows["log_rv"]
        self.last_log_realized_vol_ = y.dropna().iloc[-1]
        self.change_quantiles_ = {}
        for horizon in range(1, HORIZON + 1):
            changes = (y.shift(-horizon) - y).dropna()
            self.change_quantiles_[horizon] = np.quantile(changes, QUANTILES)

    def predict(self, target_times):
        """Returns the last observed value offset by each horizon's
        change quantiles, so the bands widen with horizon the same way
        the training changes did."""
        quantile_rows = [self.last_log_realized_vol_ + self.change_quantiles_[horizon]
                         for horizon in range(1, len(target_times) + 1)]
        return quantile_frame(quantile_rows, target_times)


@register
class SeasonalPersistence(BaseForecastModel):
    """Forecast = log RV at the same hour one day earlier. The day-ahead
    seasonal naive; the floor for a seasonal series."""
    name = "seasonal_persistence"

    def fit(self, training_rows):
        """Keeps the last 24 observed hours as the point path and takes
        one set of quantiles from the day-over-day change, shared by
        every horizon rather than fitted per horizon."""
        y = training_rows["log_rv"]
        self.last_day_ = y.iloc[-HORIZON:]          # the last 24 observed hours
        changes = (y - y.shift(HORIZON)).dropna()   # day-over-day change
        self.change_quantiles_ = np.quantile(changes, QUANTILES)

    def predict(self, target_times):
        """Returns yesterday's value at each target hour offset by the
        one set of day-over-day change quantiles, which leaves the band
        width flat across the horizon."""
        yesterday_values = self.last_day_.to_numpy()[:len(target_times)]
        quantile_rows = [yesterday_value + self.change_quantiles_
                         for yesterday_value in yesterday_values]
        return quantile_frame(quantile_rows, target_times)
