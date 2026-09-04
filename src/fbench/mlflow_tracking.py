"""MLflow logging for tournament results, writing one run per model into
a local sqlite tracking store at the repo root."""

import mlflow

from fbench.harness_config import ROOT


def log_tournament(scores, results_path, run_config):
    """Log one MLflow run per model in the scorecard, recording
    run_config as params, the horizon-averaged and horizon 1 and 24
    values of the pinball, error, coverage, and skill columns as metrics,
    and the results file as an artifact. It sets the process-wide MLflow
    tracking URI and experiment as a side effect, and it expects horizons
    1 and 24 to be present in scores."""
    # MLflow 3.x retired the plain filesystem store; local sqlite is the
    # supported zero-server backend.
    mlflow.set_tracking_uri(f"sqlite:///{(ROOT / 'mlflow.db').as_posix()}")
    mlflow.set_experiment("tournament")
    for model in scores.index.get_level_values("model").unique():
        s = scores.xs(model)
        with mlflow.start_run(run_name=model):
            mlflow.log_params({"model": model, **run_config})
            for col in ("pinball_mean", "mae", "cov50", "cov90",
                        "skill_vs_persistence"):
                mlflow.log_metric(col, float(s[col].mean()))
                mlflow.log_metric(f"{col}_h1", float(s.loc[1, col]))
                mlflow.log_metric(f"{col}_h24", float(s.loc[24, col]))
            mlflow.log_artifact(str(results_path))
