"""The HAR models, least squares on trailing daily, weekly and monthly
means of log RV, in a plain form and a seasonal one."""

from typing import ClassVar

import numpy as np

from fbench.harness_config import HORIZON, QUANTILES
from fbench.models.base_forecast_model import BaseForecastModel, quantile_frame, register

HAR_FEATURE_COLS = ["lag_1", "har_d", "har_w", "har_m"]


class _HarCore(BaseForecastModel):
    """Direct multi-horizon OLS on HAR-style trailing features. The
    seasonal variant's hod_* features are those of the ORIGIN hour,
    constant across the 24 predicted hours; the per-horizon regressions
    learn offsets FROM that anchor, which is why origin_features_ is
    reused across horizons rather than recomputed."""
    feature_columns: ClassVar[list[str]] = HAR_FEATURE_COLS

    def fit(self, training_rows):
        """Solves one least squares regression per horizon on the
        subclass feature_columns, and stores each regression's empirical
        residual quantiles, which is where this model's intervals come
        from. At each horizon the final rows, as many as the horizon is
        long, are excluded because their targets fall past the end of the
        training window."""
        X = training_rows[self.feature_columns].to_numpy()
        y = training_rows["log_rv"].to_numpy()
        intercept_column = np.ones((len(X), 1))
        self.coefficients_, self.residual_quantiles_ = {}, {}
        for horizon in range(1, HORIZON + 1):
            target = np.roll(y, -horizon)
            usable = (~np.isnan(X).any(axis=1)) & ~np.isnan(target)
            usable[-horizon:] = False
            design_matrix = np.hstack([intercept_column[usable], X[usable]])
            coefficients, *_ = np.linalg.lstsq(design_matrix, target[usable], rcond=None)
            residuals = target[usable] - design_matrix @ coefficients
            self.coefficients_[horizon] = coefficients
            self.residual_quantiles_[horizon] = np.quantile(residuals, QUANTILES)
        self.origin_features_ = training_rows[self.feature_columns].iloc[-1].to_numpy()

    def predict(self, target_times):
        """Returns the quantile frame got by adding each horizon's
        stored residual quantiles to the point forecast that horizon's
        regression gives for the single stored origin feature row."""
        quantile_rows = []
        for horizon in range(1, len(target_times) + 1):
            point_forecast = (self.coefficients_[horizon]
                              @ np.concatenate([[1.0], self.origin_features_]))
            quantile_rows.append(point_forecast + self.residual_quantiles_[horizon])
        return quantile_frame(quantile_rows, target_times)


@register
class Har(_HarCore):
    """The plain HAR model, regressing on the previous hour plus the
    trailing day, week and month means with no seasonal terms."""
    name = "har"


@register
class SeasonalHar(_HarCore):
    """HAR with the hour-of-day sine and cosine added to the regressors,
    so each horizon can learn an offset from the origin hour."""
    name = "har_seasonal"
    feature_columns: ClassVar[list[str]] = [*HAR_FEATURE_COLS, "hod_sin", "hod_cos"]
