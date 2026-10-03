"""The HAR models, least squares on trailing daily, weekly and monthly
means of log RV, in a plain form and a seasonal one."""

from typing import ClassVar

import numpy as np

from fbench.harness_config import HORIZON, QUANTILES
from fbench.models.base_forecast_model import BaseForecastModel, quantile_frame, register

BASE_COLS = ["lag_1", "har_d", "har_w", "har_m"]


class _HarCore(BaseForecastModel):
    """Direct multi-horizon OLS on HAR-style trailing features. The
    seasonal variant's hod_* features are those of the ORIGIN hour,
    constant across the 24 predicted hours; the per-horizon regressions
    learn offsets FROM that anchor, which is why x_last_ is reused
    across horizons rather than recomputed."""
    cols: ClassVar[list[str]] = BASE_COLS

    def fit(self, train):
        """Solves one least squares regression per horizon on the
        subclass cols, and stores each regression's empirical residual
        quantiles, which is where this model's intervals come from. The
        final h rows are excluded at horizon h because their targets
        fall past the end of the training window."""
        X = train[self.cols].to_numpy()
        y = train["log_rv"].to_numpy()
        ones = np.ones((len(X), 1))
        self.beta_, self.res_q_ = {}, {}
        for h in range(1, HORIZON + 1):
            yh = np.roll(y, -h)
            ok = (~np.isnan(X).any(axis=1)) & ~np.isnan(yh)
            ok[-h:] = False
            A = np.hstack([ones[ok], X[ok]])
            beta, *_ = np.linalg.lstsq(A, yh[ok], rcond=None)
            resid = yh[ok] - A @ beta
            self.beta_[h] = beta
            self.res_q_[h] = np.quantile(resid, QUANTILES)
        self.x_last_ = train[self.cols].iloc[-1].to_numpy()

    def predict(self, index):
        """Returns the quantile frame got by adding each horizon's
        stored residual quantiles to the point forecast that horizon's
        regression gives for the single stored origin feature row."""
        rows = []
        for h in range(1, len(index) + 1):
            point = self.beta_[h] @ np.concatenate([[1.0], self.x_last_])
            rows.append(point + self.res_q_[h])
        return quantile_frame(rows, index)


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
    cols: ClassVar[list[str]] = [*BASE_COLS, "hod_sin", "hod_cos"]
