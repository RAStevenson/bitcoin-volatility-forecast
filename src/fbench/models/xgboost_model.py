"""The gradient boosted tree model, XGBoost quantile regression over
the engineered feature columns."""

import pandas as pd
import xgboost as xgb

from fbench.feature_builder import FEATURE_COLS
from fbench.harness_config import HORIZON, QUANTILES
from fbench.models.base_forecast_model import BaseForecastModel, quantile_frame, register

PARAMS = {"n_estimators": 300, "max_depth": 4, "learning_rate": 0.05,
          "subsample": 0.8, "colsample_bytree": 0.8, "random_state": 7}


@register
class Gbm(BaseForecastModel):
    """Horizon-as-feature direct strategy: training rows are (features at
    origin time t, horizon h) -> log_rv[t+h]. One model per quantile,
    five total, rather than five per horizon."""
    name = "gbm"

    def fit(self, train):
        """Stacks one training row per (origin row, horizon) pair, then
        fits an XGBoost regressor under the pinball objective for each
        level in QUANTILES. Rows with any missing feature or a missing
        target at that horizon are dropped, and the final feature row is
        kept aside as the input predict will score."""
        feats = train[FEATURE_COLS]
        X_parts, y_parts = [], []
        for horizon in range(1, HORIZON + 1):
            target = train["log_rv"].shift(-horizon)
            usable = feats.notna().all(axis=1) & target.notna()
            X_horizon = feats[usable].copy()
            X_horizon["h"] = horizon
            X_parts.append(X_horizon)
            y_parts.append(target[usable])
        X = pd.concat(X_parts)
        y = pd.concat(y_parts)
        self.models_ = {}
        for level in QUANTILES:
            model = xgb.XGBRegressor(objective="reg:quantileerror",
                                     quantile_alpha=level, **PARAMS)
            model.fit(X, y)
            self.models_[level] = model
        self.x_last_ = feats.iloc[[-1]]

    def predict(self, index):
        """Scores the stored last feature row through all five quantile
        models once per horizon step, with the h feature set to that
        step, and returns the sorted quantile frame."""
        rows = []
        for horizon in range(1, len(index) + 1):
            origin_row = self.x_last_.copy()
            origin_row["h"] = horizon
            rows.append([float(self.models_[level].predict(origin_row)[0])
                         for level in QUANTILES])
        return quantile_frame(rows, index)
