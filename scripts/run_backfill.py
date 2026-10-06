"""Fetch every 1-minute BTC-USD candle the local minute store is missing,
from HISTORY_START up to now, then print the rows added and a gap report
over the whole store. It calls the Coinbase API and writes into data/, so
it is not a read-only inspection."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import argparse

from fbench.data import minute_store
from fbench.data.candle_backfill import backfill
from fbench.harness_config import MINUTE_SECONDS


def main():
    """Backfills the minute store, then prints the rows added, the store's
    total, and its gap report."""
    # No options; parsing still runs so --help prints the description
    # and an unknown flag stops the script before it touches any data.
    argparse.ArgumentParser(description=__doc__).parse_args()
    rows_added = backfill()
    stored_minutes = minute_store.load_minutes()
    print("rows added:", rows_added, "| total rows:", len(stored_minutes))
    print(minute_store.gap_report(stored_minutes, MINUTE_SECONDS))


if __name__ == "__main__":
    main()
