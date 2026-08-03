import numpy as np
import pandas as pd

from fbench.config import QCOLS, QUANTILES


def pinball(y, q, alpha):
    d = np.asarray(y) - np.asarray(q)
    return float(np.mean(np.maximum(alpha * d, (alpha - 1) * d)))


def score(results):
    rows = []
    for (model, h), g in results.dropna(subset=["y_true"]).groupby(
            ["model", "horizon"]):
        y = g["y_true"].to_numpy()
        pb = np.mean([pinball(y, g[c].to_numpy(), a)
                      for c, a in zip(QCOLS, QUANTILES)])
        e = y - g["q50"].to_numpy()
        rows.append({
            "model": model, "horizon": h, "pinball_mean": pb,
            "mae": float(np.mean(np.abs(e))),
            "rmse": float(np.sqrt(np.mean(e ** 2))),
            "cov50": float(np.mean((g["q25"] <= y) & (y <= g["q75"]))),
            "cov90": float(np.mean((g["q05"] <= y) & (y <= g["q95"]))),
            "n": len(g),
        })
    return pd.DataFrame(rows).set_index(["model", "horizon"]).sort_index()


def add_skill(scores):
    base = scores.xs("persistence")["pinball_mean"]
    out = scores.copy()
    out["skill_vs_persistence"] = 1 - out["pinball_mean"] / out.reset_index(
        "model").join(base.rename("b"))["b"].to_numpy()
    return out
