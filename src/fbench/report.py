import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from fbench.config import RESULTS_DIR


def _fig_hourly_profile(hourly, fig_prefix, value_label):
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
    _fig_hourly_profile(hourly, fig_prefix, value_label)
    _fig_pinball(scores, fig_prefix)
    path = RESULTS_DIR / out_name
    path.write_text("\n".join(lines))
    return path
