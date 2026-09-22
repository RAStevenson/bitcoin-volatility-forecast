"""The N-HiTS deep learning entrant, kept in a module of its own so the
torch stack is imported only when this model actually runs."""

import warnings

import numpy as np
import pandas as pd

from fbench.harness_config import HORIZON, QUANTILES, TRAIN_DAYS
from src.fbench.models.base_forecast_model import BaseForecastModel, quantile_frame, register

ENCODER_HOURS = 168  # one week of context per forecast


@register
class NHits(BaseForecastModel):
    """N-HiTS (hierarchical interpolation MLP stacks) via
    pytorch-forecasting, trained per origin with the native quantile loss
    so all five quantiles come from one network. Deliberately small and
    CPU-friendly: the tournament question is whether deep learning earns
    its complexity here, not how large a model can be built.

    Chosen over the library's TFT because this repo's design fence
    excludes transformers.
    """
    name = "nhits"
    train_days = TRAIN_DAYS

    def fit(self, train):
        """Trains one small N-HiTS network for three CPU epochs on the
        gap-interpolated log RV series, with a one-week encoder window
        and a quantile loss covering all five levels at once. Seeds are
        pinned at 7 and the trainer is deterministic, so a refit on the
        same window reproduces."""
        # Imports live here so the classical field never pays the torch
        # import cost (and the repo runs without torch installed unless
        # this entrant is requested).
        import lightning.pytorch as pl
        import torch
        from pytorch_forecasting import NHiTS, TimeSeriesDataSet
        from pytorch_forecasting.metrics import QuantileLoss

        torch.manual_seed(7)
        pl.seed_everything(7, workers=True, verbose=False)

        y = train["log_rv"].interpolate(limit=6).dropna()
        df = pd.DataFrame({
            "y": y.to_numpy(dtype="float32"),
            "time_idx": range(len(y)),
            "group": "series",
        })
        ds = TimeSeriesDataSet(
            df, time_idx="time_idx", target="y", group_ids=["group"],
            max_encoder_length=ENCODER_HOURS,
            max_prediction_length=HORIZON,
            time_varying_unknown_reals=["y"],
            target_normalizer="auto",
        )
        self.model_ = NHiTS.from_dataset(
            ds, loss=QuantileLoss(quantiles=QUANTILES),
            hidden_size=64, learning_rate=1e-3, log_interval=-1)
        trainer = pl.Trainer(
            max_epochs=3, accelerator="cpu", logger=False,
            enable_progress_bar=False, enable_checkpointing=False,
            enable_model_summary=False, deterministic=True)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            trainer.fit(self.model_,
                        ds.to_dataloader(train=True, batch_size=128,
                                         num_workers=0))
        self.tail_ = df.tail(ENCODER_HOURS + HORIZON).copy()
        self.ds_ = ds

    def predict(self, index):
        """Returns the quantile frame from a single forward pass over
        the encoder tail stored at fit time, trimmed to the first
        len(index) of the network's HORIZON decoder steps."""
        from pytorch_forecasting import TimeSeriesDataSet

        # Prediction window: the last encoder span plus HORIZON dummy
        # future rows the dataset needs to shape the decoder; the dummy
        # target values are never used as inputs for the future steps.
        last_idx = int(self.tail_["time_idx"].max())
        future = pd.DataFrame({
            "y": np.float32(self.tail_["y"].iloc[-1]),
            "time_idx": range(last_idx + 1, last_idx + 1 + HORIZON),
            "group": "series",
        })
        frame = pd.concat([self.tail_, future], ignore_index=True)
        pred_ds = TimeSeriesDataSet.from_dataset(
            self.ds_, frame, predict=True, stop_randomization=True)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            out = self.model_.predict(
                pred_ds.to_dataloader(train=False, batch_size=1,
                                      num_workers=0),
                mode="quantiles")
        q = out[0].cpu().numpy()[:len(index), :]
        return quantile_frame(q, index)
