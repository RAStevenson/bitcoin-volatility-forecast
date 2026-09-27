import pandas as pd

from fbench import commit_timing

HEADER = "+origin,target_time,horizon,model,q05,q25,q50,q75,q95"


def _row(origin, model):
    return f"+{origin},2026-01-01 11:00:00+00:00,1,{model},1,2,3,4,5"


LOG = "\n".join([
    "@@commit aaaaaaaaaaaa 2026-01-01T10:30:00+00:00 Daily run 2026-01-01",
    "+++ b/results/forecasts.csv",
    HEADER,
    _row("2026-01-01 10:00:00+00:00", "gbm"),
    _row("2026-01-01 10:00:00+00:00", "har"),
    # the next day's forecast lands 17 hours late, and the old rows are
    # re-added the way the whole-file rewrite used to re-add them
    "@@commit bbbbbbbbbbbb 2026-01-03T05:00:00+00:00 Daily run 2026-01-02: "
    "8 rows; trigger schedule, started 04:57 UTC",
    _row("2026-01-01 10:00:00+00:00", "gbm"),
    _row("2026-01-02 10:00:00+00:00", "gbm"),
    "-2026-01-01 10:00:00+00:00,removed,1,gbm,1,2,3,4,5",
])


def test_first_commit_wins_and_removed_lines_are_ignored():
    first = commit_timing.parse_log(LOG)
    assert len(first) == 3
    assert first[("2026-01-01 10:00:00+00:00", "gbm")][0] == "aaaaaaaaa"
    assert first[("2026-01-02 10:00:00+00:00", "gbm")][0] == "bbbbbbbbb"


def test_only_the_day_committed_after_its_first_target_hour_is_late():
    late = commit_timing.late_groups(commit_timing.parse_log(LOG))
    assert len(late) == 1
    g = late[0]
    assert g["origin"] == pd.Timestamp("2026-01-02 10:00:00+00:00")
    assert g["models"] == 1
    # deadline is origin + 2h = 12:00 on the 2nd; committed 05:00 on the 3rd
    assert g["minutes_late"] == 17 * 60
    assert g["subject"].startswith("Daily run 2026-01-02")


def test_run_note_reads_the_trigger_from_the_subject():
    note = commit_timing.run_note(
        "Daily run 2026-09-28: 192 rows; origin 10:00 UTC; trigger "
        "schedule, started 15:38 UTC")
    assert note == ("The run that committed it was started by GitHub's "
                    "scheduled trigger at 15:38 UTC.")
    assert commit_timing.run_note("Daily run 2026-09-03: 192 rows") is None
    assert commit_timing.run_note("") is None
