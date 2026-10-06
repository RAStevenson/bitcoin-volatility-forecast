import numpy as np
import pandas as pd

from fbench.data import hourly_series
from fbench.realized_volatility import hourly_realized_vol


def _minutes(start, n_minutes, log_return=0.001):
    """n_minutes minute candles from start, closes rising by a constant log return."""
    minute_times = pd.date_range(start, periods=n_minutes, freq="min", tz="UTC")
    return pd.DataFrame({"time": minute_times,
                         "close": 100 * np.exp(np.arange(n_minutes) * log_return),
                         "low": 0.0, "high": 0.0, "open": 0.0, "volume": 0.0})


def _stored(tmp_path, monkeypatch):
    """Two complete stored hours (00 and 01) written through the module's
    own save, with the module pointed at a temporary file. Returns the
    file's lines."""
    monkeypatch.setattr(hourly_series, "HOURLY_PATH", tmp_path / "hourly_rv.csv")
    seed_minutes = _minutes("2026-01-01 00:00", 120)
    hourly_series.save_hourly(hourly_realized_vol(seed_minutes.set_index("time")["close"]))
    return (tmp_path / "hourly_rv.csv").read_text().splitlines()


def test_update_appends_complete_hours_and_leaves_old_rows_unchanged(tmp_path, monkeypatch):
    before = _stored(tmp_path, monkeypatch)
    # The fetch is asked for minutes from one minute before the last stored
    # hour (01:00). It returns 00:59 through 03:20, so hours 01 and 02 are
    # complete at 03:20 and hour 03 is not.
    fetched = _minutes("2026-01-01 00:59", 142)

    def fetch(product, start, end, granularity):
        assert start == pd.Timestamp("2026-01-01 00:59", tz="UTC")
        return fetched

    now = pd.Timestamp("2026-01-01 03:20", tz="UTC")
    hourly, last_close, n_fetched = hourly_series.update_hourly(now=now, fetch=fetch)

    assert n_fetched == 142
    assert list(hourly.index) == list(pd.date_range("2026-01-01 00:00", periods=3,
                                                    freq="h", tz="UTC"))
    assert hourly["n_minutes"].iloc[2] == 60
    assert last_close == float(fetched["close"].iloc[-1])
    after = (tmp_path / "hourly_rv.csv").read_text().splitlines()
    assert after[:2] == before[:2]          # header and hour 00 untouched
    assert len(after) == 4


def test_update_with_no_new_minutes_returns_stored(tmp_path, monkeypatch):
    _stored(tmp_path, monkeypatch)
    hourly, last_close, n_fetched = hourly_series.update_hourly(
        now=pd.Timestamp("2026-01-01 02:05", tz="UTC"),
        fetch=lambda product, start, end, granularity: pd.DataFrame())
    assert n_fetched == 0
    assert len(hourly) == 2
    assert last_close == float(hourly["close"].iloc[-1])


def test_load_round_trips_index_and_columns(tmp_path, monkeypatch):
    _stored(tmp_path, monkeypatch)
    hourly = hourly_series.load_hourly()
    assert str(pd.DatetimeIndex(hourly.index).tz) == "UTC"
    assert list(hourly.columns) == hourly_series.COLUMNS
    assert hourly.index[0] == pd.Timestamp("2026-01-01 00:00", tz="UTC")
