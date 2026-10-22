import pandas as pd

from fbench.data import candle_backfill, coinbase_client, minute_store

CANDLE_COLUMNS = ["time", "low", "high", "open", "close", "volume"]


def _candles(start, n_minutes):
    minute_times = pd.date_range(start, periods=n_minutes, freq="min", tz="UTC")
    return pd.DataFrame({"time": minute_times, "low": 1.0, "high": 1.0, "open": 1.0,
                         "close": 1.0, "volume": 0.0})


def _store_in_memory(monkeypatch):
    """Point the minute store at a dict so no parquet is written."""
    saved = {}
    monkeypatch.setattr(minute_store, "load_minutes",
                        lambda: saved.get("minutes", pd.DataFrame()))
    monkeypatch.setattr(minute_store, "save_minutes",
                        lambda minutes: saved.__setitem__("minutes", minutes))
    return saved


def test_an_empty_chunk_is_skipped_not_requested_again(monkeypatch):
    saved = _store_in_memory(monkeypatch)
    monkeypatch.setattr(candle_backfill, "HISTORY_START", "2023-08-01")
    requests_made = []

    def fetch(product, start, end, granularity):
        requests_made.append((start, end))
        if start == pd.Timestamp("2023-08-01", tz="UTC"):
            return pd.DataFrame(columns=CANDLE_COLUMNS)  # Coinbase has nothing here
        return _candles(start, 3)

    now = pd.Timestamp("2023-08-01", tz="UTC") + candle_backfill.CHUNK_SPAN * 2
    rows_added = candle_backfill.backfill(verbose=False, now=now, fetch=fetch)
    assert rows_added == 3
    assert len(requests_made) == 2  # the empty first chunk was not re-requested
    assert requests_made[1][0] == pd.Timestamp("2023-08-01", tz="UTC") + candle_backfill.CHUNK_SPAN
    assert list(saved["minutes"].columns) == CANDLE_COLUMNS
    assert "ts" not in saved["minutes"].columns


def test_backfill_resumes_from_the_minute_after_the_last_saved_bar(monkeypatch):
    saved = _store_in_memory(monkeypatch)
    saved["minutes"] = _candles("2026-01-01 00:00", 60)
    starts = []

    def fetch(product, start, end, granularity):
        starts.append(start)
        return _candles(start, 2)

    candle_backfill.backfill(verbose=False, now=pd.Timestamp("2026-01-01 01:30", tz="UTC"),
                             fetch=fetch)
    assert starts == [pd.Timestamp("2026-01-01 01:00", tz="UTC")]
    assert len(saved["minutes"]) == 62


def test_fetch_candles_returns_the_time_column_even_when_empty(monkeypatch):
    monkeypatch.setattr(coinbase_client, "_get", lambda url, params: [])
    monkeypatch.setattr(coinbase_client.time, "sleep", lambda seconds: None)
    empty = coinbase_client.fetch_candles("BTC-USD", pd.Timestamp("2026-01-01", tz="UTC"),
                                          pd.Timestamp("2026-01-01 00:10", tz="UTC"), 60)
    assert empty.empty
    assert list(empty.columns) == CANDLE_COLUMNS
