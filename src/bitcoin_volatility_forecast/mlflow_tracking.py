"""MLflow logging for backtest results, writing one run per model into
a local sqlite tracking store at the repo root."""

import mlflow

from bitcoin_volatility_forecast.forecast_settings import ROOT


def log_backtest(scores, results_path, run_config):
    """Log one MLflow run per model in the scorecard, recording
    run_config as params, the horizon-averaged and horizon 1 and 24
    values of the pinball, error, coverage, and skill columns as metrics,
    and the results file as an artifact. It sets the process-wide MLflow
    tracking URI and experiment as a side effect, and it expects horizons
    1 and 24 to be present in scores."""
    # MLflow 3.x retired the plain filesystem store; local sqlite is the
    # supported zero-server backend.
    mlflow.set_tracking_uri(f"sqlite:///{(ROOT / 'mlflow.db').as_posix()}")
    mlflow.set_experiment("backtest")
    for model_name in scores.index.get_level_values("model").unique():
        model_scores = scores.xs(model_name)
        with mlflow.start_run(run_name=model_name):
            mlflow.log_params({"model": model_name, **run_config})
            for metric_name in ("pinball_mean", "mae", "cov50", "cov90",
                                "skill_vs_persistence"):
                mlflow.log_metric(metric_name,
                                  float(model_scores[metric_name].mean()))
                mlflow.log_metric(f"{metric_name}_h1",
                                  float(model_scores.loc[1, metric_name]))
                mlflow.log_metric(f"{metric_name}_h24",
                                  float(model_scores.loc[24, metric_name]))
            mlflow.log_artifact(str(results_path))
