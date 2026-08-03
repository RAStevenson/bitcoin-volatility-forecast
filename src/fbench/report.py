import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from fbench.config import RESULTS_DIR


def _fig_hourly_profile(hourly):
    prof = hourly.groupby(hourly.index.hour)["rv"].median()
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.plot(prof.index, prof.values)
    ax.set_xlabel("hour of day (UTC)")
    ax.set_ylabel("median annualized RV")
    path = RESULTS_DIR / "fig_hourly_profile.png"
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return path


def _fig_pinball(scores):
    fig, ax = plt.subplots(figsize=(8, 3))
    for model in scores.index.get_level_values("model").unique():
        s = scores.xs(model)["pinball_mean"]
        ax.plot(s.index, s.values, label=model)
    ax.set_xlabel("horizon (hours ahead)")
    ax.set_ylabel("mean pinball loss (log RV)")
    ax.legend(fontsize=7)
    path = RESULTS_DIR / "fig_pinball_by_horizon.png"
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return path


def write_report(scores, hourly, results_path):
    n_nan = int(hourly["rv"].isna().sum())
    lead = scores.groupby("model")[
        ["pinball_mean", "mae", "cov50", "cov90",
         "skill_vs_persistence"]].mean().sort_values("pinball_mean")
    h1 = scores.xs(1, level="horizon").sort_values("pinball_mean")
    h24 = scores.xs(24, level="horizon").sort_values("pinball_mean")
    lines = [
        "# Tournament report (generated)", "",
        f"Results file: {results_path.name}. All metrics on the log-RV "
        f"scale. Coverage targets: cov50 -> 0.50, cov90 -> 0.90.", "",
        "## Dataset",
        f"- hours: {len(hourly)}, span {hourly.index.min()} to "
        f"{hourly.index.max()}",
        f"- NaN target hours (data gaps, excluded from training and "
        f"scoring): {n_nan}", "",
        "## Leaderboard, mean over horizons 1-24", "",
        lead.round(4).to_markdown(), "",
        "## Horizon 1", "", h1.round(4).to_markdown(), "",
        "## Horizon 24", "", h24.round(4).to_markdown(), "",
        "![hourly profile](fig_hourly_profile.png)", "",
        "![pinball by horizon](fig_pinball_by_horizon.png)", "",
    ]
    _fig_hourly_profile(hourly)
    _fig_pinball(scores)
    path = RESULTS_DIR / "REPORT.md"
    path.write_text("\n".join(lines))
    return path
