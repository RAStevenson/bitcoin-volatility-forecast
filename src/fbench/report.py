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
    ax.set_ylabel("mean pinball loss (log scale)")
    ax.legend(fontsize=7)
    path = RESULTS_DIR / f"{fig_prefix}_pinball_by_horizon.png"
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return path


def write_report(scores, hourly, results_path, out_name="REPORT.md",
                 fig_prefix="fig", title="Tournament report",
                 value_label="median annualized RV"):
    n_nan = int(hourly["rv"].isna().sum())
    lead = scores.groupby("model")[
        ["pinball_mean", "mae", "cov50", "cov90",
         "skill_vs_persistence"]].mean().sort_values("pinball_mean")
    h1 = scores.xs(1, level="horizon").sort_values("pinball_mean")
    h24 = scores.xs(24, level="horizon").sort_values("pinball_mean")
    lines = [
        f"# {title} (generated)", "",
        f"Results file: {results_path.name}. All metrics on the log scale "
        f"of the target. Coverage targets: cov50 -> 0.50, cov90 -> 0.90.",
        "",
        "## Dataset",
        f"- hours: {len(hourly)}, span {hourly.index.min()} to "
        f"{hourly.index.max()}",
        f"- NaN target hours (data gaps, excluded from training and "
        f"scoring): {n_nan}", "",
        "## Leaderboard, mean over horizons 1-24", "",
        lead.round(4).to_markdown(), "",
        "## Horizon 1", "", h1.round(4).to_markdown(), "",
        "## Horizon 24", "", h24.round(4).to_markdown(), "",
        f"![hourly profile]({fig_prefix}_hourly_profile.png)", "",
        f"![pinball by horizon]({fig_prefix}_pinball_by_horizon.png)", "",
    ]
    _fig_hourly_profile(hourly, fig_prefix, value_label)
    _fig_pinball(scores, fig_prefix)
    path = RESULTS_DIR / out_name
    path.write_text("\n".join(lines))
    return path
