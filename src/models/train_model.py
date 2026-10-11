"""Train, compare, evaluate, and persist short-horizon NIFTY return models.

Candidate selection uses validation MAE only. The final test segment is held
out until after selection and is used for reporting and a deployment gate.
Artifacts are research outputs; they are not proof of trading profitability.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.models.baseline import (
    DATASET_PATH,
    HORIZONS,
    build_feature_frame,
    chronological_split,
)

ARTIFACT_DIR = Path("models/artifacts")
METRICS_PATH = Path("data/processed/model_training_metrics.json")
RANDOM_STATE = 42


def _candidate_factories() -> dict[str, Any]:
    """Small, deterministic candidate set suitable for the current MVP."""
    return {
        "ridge": lambda: make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
        "hist_gradient_boosting": lambda: HistGradientBoostingRegressor(
            max_iter=100,
            learning_rate=0.05,
            max_leaf_nodes=15,
            l2_regularization=1.0,
            early_stopping=False,
            random_state=RANDOM_STATE,
        ),
    }


def _metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float | int | None]:
    if len(actual) == 0 or len(actual) != len(predicted):
        raise ValueError("Metric inputs must be non-empty and have equal lengths.")
    if not np.isfinite(actual).all() or not np.isfinite(predicted).all():
        raise ValueError("Metric inputs must contain only finite values.")

    nonzero = predicted != 0
    return {
        "rows": int(len(actual)),
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(np.sqrt(mean_squared_error(actual, predicted))),
        "sign_accuracy": float(np.mean(np.sign(actual) == np.sign(predicted))),
        "directional_coverage": float(np.mean(nonzero)),
        "directional_accuracy_when_nonzero": (
            float(np.mean(np.sign(actual[nonzero]) == np.sign(predicted[nonzero])))
            if nonzero.any()
            else None
        ),
    }


def train_and_evaluate(
    dataset: pd.DataFrame,
    artifact_dir: Path = ARTIFACT_DIR,
    metrics_path: Path = METRICS_PATH,
) -> dict[str, Any]:
    """Select by validation MAE, refit on train+validation, and report test results."""
    feature_frame, feature_columns = build_feature_frame(dataset)
    # Treat infinite macro/derivative values as missing, never as valid features.
    feature_frame[feature_columns] = feature_frame[feature_columns].replace(
        [np.inf, -np.inf], np.nan
    )
    splits = chronological_split(feature_frame)
    artifact_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "model_selection_metric": "validation_mae",
        "test_split_used_for_selection": False,
        "feature_count": len(feature_columns),
        "features": feature_columns,
        "horizons": {},
        "limitations": [
            "A model that fails the zero-return benchmark is not deployment-eligible by default.",
            "Predictive metrics do not establish net profitability after execution effects.",
            "Historical point-in-time news is not included in this training pipeline.",
            "Macro availability timestamps are conservative proxies, not exact release vintages.",
        ],
    }

    for horizon in HORIZONS:
        target = f"target_return_{horizon}m"
        usable: dict[str, pd.DataFrame] = {}
        for split_name, split in splits.items():
            usable[split_name] = split.dropna(subset=feature_columns + [target])
            if usable[split_name].empty:
                raise ValueError(
                    f"No complete {split_name} rows for {target}; check feature/macro coverage."
                )

        x_train = usable["train"][feature_columns]
        y_train = usable["train"][target].to_numpy(dtype=float)
        x_val = usable["validation"][feature_columns]
        y_val = usable["validation"][target].to_numpy(dtype=float)
        x_test = usable["test"][feature_columns]
        y_test = usable["test"][target].to_numpy(dtype=float)

        if not (
            np.isfinite(x_train.to_numpy(dtype=float)).all()
            and np.isfinite(x_val.to_numpy(dtype=float)).all()
            and np.isfinite(x_test.to_numpy(dtype=float)).all()
        ):
            raise ValueError(f"Non-finite features remain after preprocessing for {target}.")

        validation_zero_metrics = _metrics(y_val, np.zeros_like(y_val))
        test_zero_metrics = _metrics(y_test, np.zeros_like(y_test))
        candidate_results: dict[str, Any] = {}
        best_name: str | None = None
        best_validation_mae = float("inf")

        for name, factory in _candidate_factories().items():
            candidate = factory()
            candidate.fit(x_train, y_train)
            candidate_metrics = _metrics(y_val, candidate.predict(x_val))
            candidate_results[name] = candidate_metrics
            if candidate_metrics["mae"] < best_validation_mae:
                best_name = name
                best_validation_mae = float(candidate_metrics["mae"])

        if best_name is None:
            raise RuntimeError(f"No candidate model was evaluated for {target}.")

        # Refit only after selecting the candidate, using train+validation.
        final_train = pd.concat([usable["train"], usable["validation"]], axis=0)
        final_model = _candidate_factories()[best_name]()
        final_model.fit(
            final_train[feature_columns],
            final_train[target].to_numpy(dtype=float),
        )
        test_metrics = _metrics(y_test, final_model.predict(x_test))

        validation_beats_zero = best_validation_mae < validation_zero_metrics["mae"]
        test_beats_zero = test_metrics["mae"] < test_zero_metrics["mae"]
        deployment_eligible = bool(validation_beats_zero and test_beats_zero)

        artifact = {
            "model": final_model,
            "model_name": best_name,
            "horizon_minutes": horizon,
            "target_column": target,
            "feature_columns": feature_columns,
            "validation_metrics": candidate_results[best_name],
            "validation_zero_return_baseline": validation_zero_metrics,
            "test_metrics": test_metrics,
            "test_zero_return_baseline": test_zero_metrics,
            "validation_beats_zero_return_baseline": bool(validation_beats_zero),
            "test_beats_zero_return_baseline": bool(test_beats_zero),
            "deployment_eligible": deployment_eligible,
        }
        artifact_path = artifact_dir / f"nifty_return_{horizon}m.joblib"
        joblib.dump(artifact, artifact_path)

        report["horizons"][f"{horizon}m"] = {
            "selected_model": best_name,
            "train_rows": int(len(usable["train"])),
            "validation_rows": int(len(usable["validation"])),
            "test_rows": int(len(usable["test"])),
            "candidate_validation_metrics": candidate_results,
            "validation_zero_return_baseline": validation_zero_metrics,
            "test_metrics": test_metrics,
            "test_zero_return_baseline": test_zero_metrics,
            "validation_beats_zero_return_baseline": bool(validation_beats_zero),
            "test_beats_zero_return_baseline": bool(test_beats_zero),
            "deployment_eligible": deployment_eligible,
            "artifact_path": str(artifact_path),
        }

    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    if not DATASET_PATH.is_file():
        raise FileNotFoundError(
            f"Training dataset not found: {DATASET_PATH}. "
            "Run python -m src.data_engineering.create_targets first."
        )

    report = train_and_evaluate(pd.read_csv(DATASET_PATH))
    print("Project Alpha — model training and evaluation")
    print("Candidate selection uses validation MAE; test data is not used for selection.")
    for horizon, result in report["horizons"].items():
        model_metrics = result["test_metrics"]
        zero_metrics = result["test_zero_return_baseline"]
        improvement = (
            (1 - model_metrics["mae"] / zero_metrics["mae"]) * 100
            if zero_metrics["mae"] > 0
            else float("nan")
        )
        print(
            f"{horizon}: model={result['selected_model']}, "
            f"test_MAE={model_metrics['mae']:.8f}, "
            f"zero_MAE={zero_metrics['mae']:.8f}, "
            f"MAE_improvement={improvement:.2f}%, "
            f"deployment_eligible={result['deployment_eligible']}"
        )
    print(f"Metrics saved to {METRICS_PATH}")
    print(f"Model artifacts saved to {ARTIFACT_DIR}")


if __name__ == "__main__":
    main()
