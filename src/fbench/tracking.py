import mlflow

from fbench.config import ROOT


def log_tournament(scores, results_path, run_config):
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
