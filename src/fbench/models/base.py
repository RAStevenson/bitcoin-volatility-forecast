from abc import ABC, abstractmethod

import numpy as np
import pandas as pd

from fbench.config import QCOLS, TRAIN_DAYS

REGISTRY = {}


def register(cls):
    REGISTRY[cls.name] = cls
    return cls


class ForecastModel(ABC):
    name = "base"
    train_days = TRAIN_DAYS

    @abstractmethod
    def fit(self, train):
        ...

    @abstractmethod
    def predict(self, index):
        ...


def quantile_frame(values, index):
    """values: (len(index), 5) array. Sorts each row so quantiles never
    cross (standard fix for independently produced quantiles)."""
    return pd.DataFrame(np.sort(np.asarray(values, dtype=float), axis=1),
                        index=index, columns=QCOLS)
