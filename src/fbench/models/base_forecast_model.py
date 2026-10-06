"""The contract every forecast model in this package implements, along
with the name registry the backtest and the daily runner look models up
in."""

from abc import ABC, abstractmethod

import numpy as np
import pandas as pd

from fbench.harness_config import QCOLS, TRAIN_DAYS

REGISTRY = {}


def register(model_class):
    """Files the decorated model class in REGISTRY under its own name
    attribute and hands it back unchanged. Importing the module is what
    registers it, so a model absent from an entry script's imports is
    invisible to the runners."""
    REGISTRY[model_class.name] = model_class
    return model_class


class BaseForecastModel(ABC):
    """Abstract model, fixing the fit-then-predict pair that the
    backtest and the daily runner drive every model through. A subclass
    sets name for the registry, and overrides train_days when it wants a
    shorter training window than the project default."""
    name = "base"
    train_days = TRAIN_DAYS

    @abstractmethod
    def fit(self, training_rows):
        """Estimates the model on training_rows, a feature frame ending at
        the forecast origin, and stashes on the instance whatever predict
        needs. Every row of training_rows is at or before the origin, so a
        fit may use the whole frame without leaking."""
        ...

    @abstractmethod
    def predict(self, target_times):
        """Returns a DataFrame indexed by target_times carrying the five
        QCOLS quantile columns, one row per target timestamp. Rows run in
        horizon order with h=1 first, and target_times never holds more
        than HORIZON timestamps."""
        ...


def quantile_frame(quantile_values, target_times):
    """quantile_values: (len(target_times), 5) array. Sorts each row so
    quantiles never cross (standard fix for independently produced
    quantiles)."""
    return pd.DataFrame(np.sort(np.asarray(quantile_values, dtype=float), axis=1),
                        index=target_times, columns=QCOLS)
