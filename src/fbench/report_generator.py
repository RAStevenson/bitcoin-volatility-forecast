"""Builds the backtest tournament report, results/REPORT.md for the
volatility run and results/LOAD_REPORT.md for the load demo, which is
what a reader compares models on before any live scores exist. Tables and
figures are rendered from a run's scored rows, and the Dataset section is
pinned to the snapshot that run recorded rather than to today's data."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from fbench.harness_config import RESULTS_DIR


def _fig_hourly_profile(hourly, fig_prefix, value_label):
    """Save the median-by-hour-of-day curve into results/ as
    <fig_prefix>_hourly_profile.png and return its path, giving the report
    the daily shape its horizon curve turns out to inherit."""
    prof = hourly.groupby(hourly.index.hour)["rv"].median()
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.plot(prof.index, prof.values)
    ax.set_xlabel("hour of day (UTC)")
    ax.set_ylabel(value_label)
    path = RESULTS_DIR / f"{fig_prefix}_hourly_profile.png"
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return path


def _fig_pinball(scores, fig_prefix):
    """Save one pinball-loss-against-horizon line per model into results/
    as <fig_prefix>_pinball_by_horizon.png and return its path."""
    fig, ax = plt.subplots(figsize=(8, 3))
    for model in scores.index.get_level_values("model").unique():
        s = scores.xs(model)["pinball_mean"]
        ax.plot(s.index, s.values, label=model)
    ax.set_xlabel("horizon (hours ahead)")
    ax.set_ylabel("mean pinball loss (log-scale target)")
    ax.legend(fontsize=7)
    path = RESULTS_DIR / f"{fig_prefix}_pinball_by_horizon.png"
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return path


def write_report(scores, hourly, results_path, out_name="REPORT.md",
                 fig_prefix="fig", title="Tournament report",
                 value_label="median annualized RV", dataset_stats=None):
    """Write the tournament report and its two figures into results/ and
    return the report path, giving the reader a leaderboard averaged over
    horizons 1 to 24, the horizon 1 and horizon 24 tables, and the caveats
    this run's numbers need. Without dataset_stats the Dataset section
    describes the hourly file as it stands now rather than the data the
    backtest actually saw."""
    # dataset_stats pins the Dataset section to the data the backtest
    # actually saw (recorded in the run's json sidecar at backtest time).
    # Without it the section describes whatever the hourly file holds at
    # render time, which drifts as the daily loop grows the dataset.
    if dataset_stats is None:
        dataset_stats = {
            "dataset_hours": len(hourly),
            "dataset_span_start": str(hourly.index.min()),
            "dataset_span_end": str(hourly.index.max()),
            "dataset_nan_hours": int(hourly["rv"].isna().sum()),
        }
    lead = scores.groupby("model")[
        ["pinball_mean", "mae", "cov50", "cov90",
         "skill_vs_persistence"]].mean().sort_values("pinball_mean")
    h1 = scores.xs(1, level="horizon").sort_values("pinball_mean")
    h24 = scores.xs(24, level="horizon").sort_values("pinball_mean")
    lines = [
        f"# {title} (generated)", "",
        f"Results file: {results_path.name}. All metrics are on the log "
        f"scale of the target. Coverage targets: cov50 -> 0.50, "
        f"cov90 -> 0.90. skill_vs_persistence is the mean of per-horizon "
        f"skill scores, so a model can rank differently on skill than on "
        f"pinball_mean; horizons where persistence does worst weigh most.",
        "",
        "## Dataset",
        f"- hours: {dataset_stats['dataset_hours']}, span "
        f"{dataset_stats['dataset_span_start']} to "
        f"{dataset_stats['dataset_span_end']}",
        f"- NaN target hours (data gaps, excluded from training and "
        f"scoring): {dataset_stats['dataset_nan_hours']}", "",
        "## Leaderboard, mean over horizons 1-24", "",
        lead.round(4).to_markdown(), "",
        "## Horizon 1", "", h1.round(4).to_markdown(), "",
        "## Horizon 24", "", h24.round(4).to_markdown(), "",
    ]
    if {"persistence", "seasonal_persistence"} <= set(h24.index):
        lines += [
            "The identical persistence and seasonal_persistence rows at "
            "horizon 24 are by construction: there the seasonal lag is the "
            "same last observed hour, and both bands draw on the same "
            "24-hour change distribution.", "",
        ]
    if h1["n"].nunique() > 1 or h24["n"].nunique() > 1:
        lines += [
            "Where a model's n falls short of the maximum, rows whose "
            "forecast came back NaN (a degenerate fit) were dropped "
            "before scoring, so per-model samples differ slightly there.",
            "",
        ]
    lines += [
        f"![hourly profile]({fig_prefix}_hourly_profile.png)", "",
        f"![pinball by horizon]({fig_prefix}_pinball_by_horizon.png)", "",
    ]
    # Origins are floored to 00:00 UTC by make_origins, so horizon h always
    # scores the same clock hour and the two figures above are confounded
    # by construction. Computed at render time because the correlation is
    # specific to this run's scores and data.
    by_h = scores.groupby("horizon")["pinball_mean"].mean()
    prof = hourly.groupby(hourly.index.hour)["rv"].median()
    hour_r = float(np.corrcoef(
        by_h.to_numpy(),
        prof.reindex([h % 24 for h in by_h.index]).to_numpy())[0, 1])
    lines += [
        f"Backtest origins all sit at 00:00 UTC, so a given horizon always "
        f"lands on the same UTC clock hour, and the pinball-by-horizon "
        f"curve inherits the hour-of-day profile above (correlation "
        f"{hour_r:.2f} between the two curves on this run). A bump at one "
        f"horizon is largely that clock hour showing through, not a "
        f"property of forecasting that far ahead.", "",
    ]
    _fig_hourly_profile(hourly, fig_prefix, value_label)
    _fig_pinball(scores, fig_prefix)
    path = RESULTS_DIR / out_name
    path.write_text("\n".join(lines))
    return path
