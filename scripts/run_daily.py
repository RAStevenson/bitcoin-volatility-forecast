"""Run the daily loop end to end, backfilling minutes, rebuilding
the hourly realized volatility series, resolving the forecasts whose
target hour has closed, logging a fresh 24-hour forecast for every
registered model, regenerating the three reports (the review with the
outlook's claims scored), and committing and pushing the result."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import subprocess

import pandas as pd

# Import all model modules so the registry is complete for the daily fits.
import fbench.models.xgboost_model  # noqa: F401
import fbench.models.har_model  # noqa: F401
import fbench.models.nhits_model  # noqa: F401  (added 2026-08-06 after it led
#   the 2026-08-05 full tournament)
import fbench.models.persistence_model  # noqa: F401
import fbench.models.prophet_model  # noqa: F401
import fbench.models.sarima_model  # noqa: F401
from fbench import live_loop
from fbench.harness_config import DATA_DIR, ROOT
from fbench.data import minute_store
from fbench.data.candle_backfill import backfill
from fbench.feature_builder import build_features
from fbench.realized_volatility import hourly_realized_vol


def step(name, fn):
    """Runs one named stage of the loop, printing the name first and
    exiting with a message naming that stage if it raises, so a failed
    overnight run says where it stopped."""
    print(f"[daily] {name}", flush=True)
    try:
        return fn()
    except Exception as e:
        sys.exit(f"[daily] FAILED at step '{name}': {e}")


added = step("backfill", lambda: backfill(verbose=False))
print(f"  minutes added: {added}")


def _build_rv():
    """Rebuilds the hourly realized volatility series from the minute
    store and saves it, returning it with the latest minute close that
    the outlook needs to quote moves in dollars."""
    m = minute_store.load_minutes()
    out = hourly_realized_vol(m.set_index("time")["close"])
    out.to_parquet(DATA_DIR / "hourly_rv.parquet")
    return out, float(m.loc[m["time"].idxmax(), "close"])


hourly, last_close = step("rebuild rv", _build_rv)
resolved = step("score due", lambda: live_loop.score_due(hourly))
print(f"  rows resolved: {resolved}")

feats = build_features(hourly)
origin = hourly["log_rv"].dropna().index[-1]
logged = step("log forecasts", lambda: live_loop.log_forecasts(feats, origin))
print(f"  forecast rows logged: {logged} (origin {origin})")
step("live report", live_loop.write_live_report)
from fbench.outlook_generator import write_outlook  # noqa: E402
step("outlook", lambda: write_outlook(hourly, last_price=last_close))
from fbench.review_generator import write_review  # noqa: E402
step("review", lambda: write_review(hourly))


def _commit_push():
    """Commits the regenerated logs and reports, pushing when an origin
    remote is configured. Committing happens before the logged target
    hours close, which is what makes the forecast log pre-outcome
    evidence. A second run on the same day finds nothing staged and
    returns without committing."""
    day = pd.Timestamp.now(tz="UTC").date()
    tracked = [p for p in ("results/forecasts.csv", "results/evaluation.csv",
                           "results/LIVE.md", "results/OUTLOOK.md",
                           "results/REVIEW.md")
               if (ROOT / p).exists()]
    subprocess.run(["git", "add", *tracked], cwd=ROOT, check=True)
    diff = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT)
    if diff.returncode == 0:
        print("  nothing new to commit (already ran today)")
        return
    subprocess.run(["git", "commit", "-m",
                    f"Daily run {day}: {logged} forecast rows logged, "
                    f"{resolved} resolved"], cwd=ROOT, check=True)
    remotes = subprocess.run(["git", "remote"], cwd=ROOT,
                             capture_output=True, text=True).stdout.split()
    if "origin" in remotes:
        subprocess.run(["git", "push", "origin", "HEAD"], cwd=ROOT,
                       check=True)
        print("  committed and pushed")
    else:
        print("  committed; no remote configured, push skipped")


step("commit and push", _commit_push)
print("[daily] done")
