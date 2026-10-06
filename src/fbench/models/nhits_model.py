"""The N-HiTS deep learning model, kept in a module of its own so the
torch stack is imported only when this model actually runs."""

import warnings
from typing import cast

import numpy as np
import pandas as pd

from fbench.harness_config import HORIZON, QUANTILES, TRAIN_DAYS
from fbench.models.base_forecast_model import BaseForecastModel, quantile_frame, register

ENCODER_HOURS = 168  # one week of context per forecast

# The only warnings this module blocks, each matched by the start of its
# message so that any other warning still prints. All five are raised on
# every call to fit, and the last two again on every call to predict.
# Each has a reason it does not apply here.
BLOCKED_WARNINGS = (
    # Advice on what to leave out of a checkpoint file. This model
    # writes no checkpoints (enable_checkpointing=False in fit).
    (r"Attribute '(loss|logging_metrics)' is an instance of `nn\.Module` "
     r"and is already saved during checkpointing", UserWarning),
    # The network trains for a fixed three epochs on the whole training
    # window with no validation set, so there is no validation loop to
    # run.
    (r"You defined a `validation_step` but have no `val_dataloader`",
     UserWarning),
    # The library attaches a scheduler that lowers the learning rate
    # when the validation loss stops improving. With no validation set
    # it has nothing to read, so the rate stays at the 1e-3 set in fit
    # for all three epochs, which is the training intended.
    (r"ReduceLROnPlateau conditioned on metric val_loss which is not "
     r"available", RuntimeWarning),
    # The data loaders run in the main process on purpose
    # (num_workers=0): the training data is one series of about 8,800
    # hourly values already in memory.
    (r"The '(train|predict)_dataloader' does not have many workers",
     UserWarning),
    # Raised inside Lightning about its own call into torch, not about
    # code in this repo. Both versions are pinned in requirements.txt;
    # delete this entry when a newer Lightning stops raising it.
    (r"`isinstance\(treespec, LeafSpec\)` is deprecated", FutureWarning),
)


def _block_listed_warnings():
    """Adds an ignore filter for each entry of BLOCKED_WARNINGS to the
    enclosing warnings.catch_warnings block, leaving every other warning
    to print."""
    for message, category in BLOCKED_WARNINGS:
        warnings.filterwarnings("ignore", message=message, category=category)


@register
class NHits(BaseForecastModel):
    """N-HiTS (hierarchical interpolation MLP stacks) via
    pytorch-forecasting, trained per origin with the native quantile loss
    so all five quantiles come from one network. Deliberately small and
    CPU-friendly: the backtest question is whether deep learning earns
    its complexity here, not how large a model can be built.

    Chosen over the library's TFT because this repo's design fence
    excludes transformers.
    """
    name = "nhits"
    train_days = TRAIN_DAYS

    def fit(self, training_rows):
        """Trains one small N-HiTS network for three CPU epochs on the
        gap-interpolated log RV series, with a one-week encoder window
        and a quantile loss covering all five levels at once. Seeds are
        pinned at 7 and the trainer is deterministic, so a refit on the
        same window reproduces."""
        # Imports live here so the classical field never pays the torch
        # import cost (and the repo runs without torch installed unless
        # this model is requested).
        import lightning.pytorch as pl
        import torch
        from pytorch_forecasting import NHiTS, TimeSeriesDataSet
        from pytorch_forecasting.metrics import QuantileLoss

        torch.manual_seed(7)
        pl.seed_everything(7, workers=True, verbose=False)

        y = training_rows["log_rv"].interpolate(limit=6).dropna()
        series_frame = pd.DataFrame({
            "y": y.to_numpy(dtype="float32"),
            "time_idx": range(len(y)),
            "group": "series",
        })
        dataset = TimeSeriesDataSet(
            series_frame, time_idx="time_idx", target="y", group_ids=["group"],
            max_encoder_length=ENCODER_HOURS,
            max_prediction_length=HORIZON,
            time_varying_unknown_reals=["y"],
            target_normalizer="auto",
        )
        with warnings.catch_warnings():
            _block_listed_warnings()
            # from_dataset is declared as returning the Lightning base
            # class; it builds an NHiTS, which is what predict is called
            # on below.
            self.model_ = cast(NHiTS, NHiTS.from_dataset(
                dataset, loss=QuantileLoss(quantiles=QUANTILES),
                hidden_size=64, learning_rate=1e-3, log_interval=-1))
            trainer = pl.Trainer(
                max_epochs=3, accelerator="cpu", logger=False,
                enable_progress_bar=False, enable_checkpointing=False,
                enable_model_summary=False, deterministic=True)
            trainer.fit(self.model_,
                        dataset.to_dataloader(train=True, batch_size=128,
                                              num_workers=0))
        self.series_tail_ = series_frame.tail(ENCODER_HOURS + HORIZON).copy()
        self.dataset_ = dataset

    def predict(self, target_times):
        """Returns the quantile frame from a single forward pass over
        the encoder tail stored at fit time, trimmed to the first
        len(target_times) of the network's HORIZON decoder steps."""
        from pytorch_forecasting import TimeSeriesDataSet

        # Prediction window: the last encoder span plus HORIZON dummy
        # future rows the dataset needs to shape the decoder; the dummy
        # target values are never used as inputs for the future steps.
        last_time_step = int(self.series_tail_["time_idx"].max())
        future = pd.DataFrame({
            "y": np.float32(self.series_tail_["y"].iloc[-1]),
            "time_idx": range(last_time_step + 1, last_time_step + 1 + HORIZON),
            "group": "series",
        })
        prediction_frame = pd.concat([self.series_tail_, future], ignore_index=True)
        prediction_dataset = TimeSeriesDataSet.from_dataset(
            self.dataset_, prediction_frame, predict=True, stop_randomization=True)
        with warnings.catch_warnings():
            _block_listed_warnings()
            network_quantiles = self.model_.predict(
                prediction_dataset.to_dataloader(train=False, batch_size=1,
                                                 num_workers=0),
                mode="quantiles",
                # predict builds a Trainer of its own; without these it
                # writes lightning_logs/version_N/hparams.yaml per call.
                trainer_kwargs={"logger": False, "accelerator": "cpu",
                                "enable_progress_bar": False,
                                "enable_model_summary": False})
        quantile_values = network_quantiles[0].cpu().numpy()[:len(target_times), :]
        return quantile_frame(quantile_values, target_times)
