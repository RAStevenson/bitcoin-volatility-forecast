"""The gradient boosted tree model, XGBoost quantile regression over
the engineered feature columns."""

import pandas as pd
import xgboost as xgb

from fbench.harness_config import HORIZON, QUANTILES
from fbench.feature_builder import FEATURE_COLS
from fbench.models.base_forecast_model import BaseForecastModel, quantile_frame, register

PARAMS = dict(n_estimators=300, max_depth=4, learning_rate=0.05,
              subsample=0.8, colsample_bytree=0.8, random_state=7)


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
        h-step target are dropped, and the final feature row is kept
        aside as the input predict will score."""
        feats = train[FEATURE_COLS]
        X_parts, y_parts = [], []
        for h in range(1, HORIZON + 1):
            target = train["log_rv"].shift(-h)
            ok = feats.notna().all(axis=1) & target.notna()
            Xh = feats[ok].copy()
            Xh["h"] = h
            X_parts.append(Xh)
            y_parts.append(target[ok])
        X = pd.concat(X_parts)
        y = pd.concat(y_parts)
        self.models_ = {}
        for q in QUANTILES:
            m = xgb.XGBRegressor(objective="reg:quantileerror",
                                 quantile_alpha=q, **PARAMS)
            m.fit(X, y)
            self.models_[q] = m
        self.x_last_ = feats.iloc[[-1]]

    def predict(self, index):
        """Scores the stored last feature row through all five quantile
        models once per horizon step, with the h feature set to that
        step, and returns the sorted quantile frame."""
        rows = []
        for h in range(1, len(index) + 1):
            xrow = self.x_last_.copy()
            xrow["h"] = h
            rows.append([float(self.models_[q].predict(xrow)[0])
                         for q in QUANTILES])
        return quantile_frame(rows, index)
