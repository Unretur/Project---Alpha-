
"""Compare Project Alpha's Ridge model with a zero-return baseline."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error

from src.models.baseline import (
    DATASET_PATH,
    METRICS_PATH,
    HORIZONS,
    build_feature_frame,
    chronological_split,
    _metrics,
)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge


def evaluate_predictions(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Measure return error and directional prediction behaviour."""
    nonzero_direction = y_pred != 0

    result = {
        "rows": int(len(y_true)),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "exact_sign_accuracy_including_zero": float(
            np.mean(np.sign(y_true) == np.sign(y_pred))
        ),
        "directional_coverage": float(np.mean(nonzero_direction)),
    }

    if nonzero_direction.any():
        result["directional_accuracy_when_nonzero"] = float(
            np.mean(np.sign(y_true[nonzero_direction]) == np.sign(y_pred[nonzero_direction]))
        )
    else:
        result["directional_accuracy_when_nonzero"] = None

    return result


def main() -> None:
    if not DATASET_PATH.is_file():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")

    dataset = pd.read_csv(DATASET_PATH)
    feature_frame, feature_columns = build_feature_frame(dataset)
    splits = chronological_split(feature_frame)

    print("Project Alpha — Evaluation diagnostics")
    print(f"Feature count: {len(feature_columns)}")

    for horizon in HORIZONS:
        target = f"target_return_{horizon}m"
        train = splits["train"].dropna(subset=feature_columns + [target])
        test = splits["test"].dropna(subset=feature_columns + [target])

        if train.empty or test.empty:
            print(f"\n{horizon}m: insufficient usable rows; skipped.")
            continue

        model = make_pipeline(StandardScaler(), Ridge(alpha=1.0))
        model.fit(train[feature_columns], train[target])

        y_true = test[target].to_numpy()
        ridge_prediction = model.predict(test[feature_columns])
        zero_prediction = np.zeros_like(y_true)

        ridge_metrics = evaluate_predictions(y_true, ridge_prediction)
        zero_metrics = evaluate_predictions(y_true, zero_prediction)

        print(f"\n{'=' * 55}")
        print(f"Horizon: {horizon} minutes")
        print(f"Test rows: {len(test)}")
        print(f"Ridge MAE: {ridge_metrics['mae']:.8f}")
        print(f"Zero-baseline MAE: {zero_metrics['mae']:.8f}")
        print(
            "Ridge MAE improvement (%): "
            f"{(1 - ridge_metrics['mae'] / zero_metrics['mae']) * 100:.2f}%"
        )
        print(
            "Ridge sign accuracy (including zero): "
            f"{ridge_metrics['exact_sign_accuracy_including_zero']:.2%}"
        )
        print(
            "Ridge directional accuracy (non-zero predictions): "
            f"{ridge_metrics['directional_accuracy_when_nonzero']}"
        )
        print(
            "Ridge directional coverage: "
            f"{ridge_metrics['directional_coverage']:.2%}"
        )
        print(
            "Zero-baseline exact sign accuracy: "
            f"{zero_metrics['exact_sign_accuracy_including_zero']:.2%}"
        )


if __name__ == "__main__":
    main()
