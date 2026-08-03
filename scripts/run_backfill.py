import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from fbench.config import MINUTE_SECONDS
from fbench.data import store
from fbench.data.backfill import backfill

added = backfill()
final = store.load_minutes()
print("rows added:", added, "| total rows:", len(final))
print(store.gap_report(final, MINUTE_SECONDS))
