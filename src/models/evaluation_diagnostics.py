"""Compare the Ridge model with a zero-return baseline on the held-out test split."""

import numpy as np
import pandas as pd
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


def evaluate_predictions(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Measure return errors and directional behaviour without hiding coverage."""
    if len(y_true) == 0 or len(y_pred) == 0:
        raise ValueError("Evaluation requires at least one prediction.")
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length.")

    nonzero_prediction = y_pred != 0
    result = {
        "rows": int(len(y_true)),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "sign_accuracy": float(np.mean(np.sign(y_true) == np.sign(y_pred))),
        "directional_coverage": float(np.mean(nonzero_prediction)),
    }

    if nonzero_prediction.any():
        result["directional_accuracy_when_nonzero"] = float(
            np.mean(
                np.sign(y_true[nonzero_prediction])
                == np.sign(y_pred[nonzero_prediction])
            )
        )
    else:
        result["directional_accuracy_when_nonzero"] = None

    return result


def main() -> None:
    if not DATASET_PATH.is_file():
        raise FileNotFoundError(
            f"Dataset not found: {DATASET_PATH}. "
            "Run python -m src.data_engineering.create_targets first."
        )

    dataset = pd.read_csv(DATASET_PATH)
    feature_frame, feature_columns = build_feature_frame(dataset)
    splits = chronological_split(feature_frame)

    print("Project Alpha — Evaluation diagnostics")
    print(f"Feature count: {len(feature_columns)}")
    print("The test split is held out; no model tuning is performed here.")

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
        zero_mae = zero_metrics["mae"]
        mae_improvement = (
            (1 - ridge_metrics["mae"] / zero_mae) * 100
            if zero_mae > 0
            else float("nan")
        )

        print(f"\n{'=' * 55}")
        print(f"Horizon: {horizon} minutes")
        print(f"Test rows: {len(test)}")
        print(f"Ridge MAE: {ridge_metrics['mae']:.8f}")
        print(f"Zero-return MAE: {zero_mae:.8f}")
        print(f"Ridge MAE improvement vs zero (%): {mae_improvement:.2f}")
        print(f"Ridge sign accuracy: {ridge_metrics['sign_accuracy']:.2%}")
        directional_accuracy = ridge_metrics["directional_accuracy_when_nonzero"]
        if directional_accuracy is None:
            print("Ridge directional accuracy when non-zero: N/A (no non-zero predictions)")
        else:
            print(f"Ridge directional accuracy when non-zero: {directional_accuracy:.2%}")
        print(f"Ridge directional coverage: {ridge_metrics['directional_coverage']:.2%}")
        print(
            "Interpretation: these are research diagnostics, not evidence of "
            "a profitable trading strategy."
        )


if __name__ == "__main__":
    main()
