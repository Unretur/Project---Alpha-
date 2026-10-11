"""Expanding-window walk-forward evaluation for Project Alpha.

This is a research diagnostic, not a trading simulator. Each fold trains only
on earlier rows, purges training labels whose forward horizon could cross the
fold boundary, and compares Ridge with a zero-return MAE baseline.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

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
)

DEFAULT_REPORT_PATH = Path("data/processed/walk_forward_metrics.json")
DEFAULT_N_SPLITS = 4
DEFAULT_MIN_TRAIN_FRACTION = 0.50


def _metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float | int]:
    if len(actual) == 0 or len(actual) != len(predicted):
        raise ValueError("Metric inputs must be non-empty and have equal lengths.")
    return {
        "rows": int(len(actual)),
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(np.sqrt(mean_squared_error(actual, predicted))),
        "directional_accuracy": float(
            np.mean(np.sign(actual) == np.sign(predicted))
        ),
    }


def evaluate_walk_forward(
    dataset: pd.DataFrame,
    n_splits: int = DEFAULT_N_SPLITS,
    min_train_fraction: float = DEFAULT_MIN_TRAIN_FRACTION,
    selected_features: list[str] | None = None,
) -> dict[str, Any]:
    """Evaluate each horizon across sequential test windows with expanding history."""
    if n_splits < 2:
        raise ValueError("n_splits must be at least 2.")
    if not 0 < min_train_fraction < 1:
        raise ValueError("min_train_fraction must be between 0 and 1.")

    feature_frame, available_features = build_feature_frame(dataset)
    if selected_features is None:
        feature_columns = available_features
    else:
        if not selected_features:
            raise ValueError("selected_features must not be empty.")
        missing_features = set(selected_features).difference(available_features)
        if missing_features:
            raise ValueError(
                f"Unknown selected features: {sorted(missing_features)}"
            )
        if len(set(selected_features)) != len(selected_features):
            raise ValueError("selected_features must not contain duplicates.")
        feature_columns = list(selected_features)

    feature_frame[feature_columns] = feature_frame[feature_columns].replace(
        [np.inf, -np.inf], np.nan
    )
    ordered = feature_frame.sort_values("timestamp").reset_index(drop=True)
    n_rows = len(ordered)
    first_test_index = int(n_rows * min_train_fraction)
    if n_rows - first_test_index < n_splits:
        raise ValueError("Not enough rows for the requested walk-forward folds.")

    boundaries = np.linspace(
        first_test_index, n_rows, num=n_splits + 1, dtype=int
    )
    if len(set(boundaries)) != len(boundaries):
        raise ValueError("Not enough rows to create distinct test folds.")

    report: dict[str, Any] = {
        "method": "expanding_window_walk_forward",
        "n_splits": n_splits,
        "min_train_fraction": min_train_fraction,
        "selection_used_test_folds": False,
        "feature_count": len(feature_columns),
        "features": feature_columns,
        "horizons": {},
        "limitations": [
            "Research evaluation only; it does not simulate execution or net profitability.",
            "Macro availability timestamps are conservative proxies, not exact release vintages.",
            "Historical point-in-time news features are not included.",
            "Fold metrics are correlated observations and are not independent trials.",
        ],
    }

    for horizon in HORIZONS:
        target = f"target_return_{horizon}m"
        fold_results: list[dict[str, Any]] = []
        all_actual: list[np.ndarray] = []
        all_predictions: list[np.ndarray] = []
        all_zero: list[np.ndarray] = []

        for fold_index in range(n_splits):
            test_start_index = int(boundaries[fold_index])
            test_end_index = int(boundaries[fold_index + 1])
            test_start = ordered.loc[test_start_index, "timestamp"]
            test_end = (
                ordered.loc[test_end_index, "timestamp"]
                if test_end_index < n_rows
                else None
            )

            # Purge earlier training labels whose forward horizon reaches the
            # test boundary. The comparison uses elapsed time, not row counts.
            train = ordered.loc[
                ordered["timestamp"] + pd.Timedelta(minutes=horizon) < test_start
            ]
            test_mask = ordered["timestamp"] >= test_start
            if test_end is not None:
                test_mask &= ordered["timestamp"] < test_end
            test = ordered.loc[test_mask]

            train = train.dropna(subset=feature_columns + [target])
            test = test.dropna(subset=feature_columns + [target])
            if train.empty or test.empty:
                raise ValueError(
                    f"Insufficient usable rows for {horizon}m fold {fold_index + 1}: "
                    f"train={len(train)}, test={len(test)}."
                )

            x_train = train[feature_columns].to_numpy(dtype=float)
            x_test = test[feature_columns].to_numpy(dtype=float)
            y_train = train[target].to_numpy(dtype=float)
            y_test = test[target].to_numpy(dtype=float)
            if not (
                np.isfinite(x_train).all()
                and np.isfinite(x_test).all()
                and np.isfinite(y_train).all()
                and np.isfinite(y_test).all()
            ):
                raise ValueError(
                    f"Non-finite values remain in {horizon}m fold {fold_index + 1}."
                )

            model = make_pipeline(StandardScaler(), Ridge(alpha=1.0))
            model.fit(x_train, y_train)
            prediction = model.predict(x_test)
            zero = np.zeros_like(y_test)
            model_metrics = _metrics(y_test, prediction)
            zero_metrics = _metrics(y_test, zero)
            improvement = (
                (1 - model_metrics["mae"] / zero_metrics["mae"]) * 100
                if zero_metrics["mae"] > 0
                else None
            )
            fold_results.append(
                {
                    "fold": fold_index + 1,
                    "train_rows": int(len(train)),
                    "test_rows": int(len(test)),
                    "train_end": train["timestamp"].max().isoformat(),
                    "test_start": test["timestamp"].min().isoformat(),
                    "test_end": test["timestamp"].max().isoformat(),
                    "model_metrics": model_metrics,
                    "zero_return_baseline": zero_metrics,
                    "mae_improvement_pct": improvement,
                    "beats_zero_return_baseline": bool(
                        model_metrics["mae"] < zero_metrics["mae"]
                    ),
                }
            )
            all_actual.append(y_test)
            all_predictions.append(prediction)
            all_zero.append(zero)

        actual = np.concatenate(all_actual)
        prediction = np.concatenate(all_predictions)
        zero_prediction = np.concatenate(all_zero)
        aggregate_model = _metrics(actual, prediction)
        aggregate_zero = _metrics(actual, zero_prediction)
        report["horizons"][f"{horizon}m"] = {
            "folds": fold_results,
            "aggregate_model_metrics": aggregate_model,
            "aggregate_zero_return_baseline": aggregate_zero,
            "aggregate_mae_improvement_pct": (
                (1 - aggregate_model["mae"] / aggregate_zero["mae"]) * 100
                if aggregate_zero["mae"] > 0
                else None
            ),
            "folds_beating_zero_baseline": sum(
                fold["beats_zero_return_baseline"] for fold in fold_results
            ),
        }

    return report


def main() -> None:
    if not DATASET_PATH.is_file():
        raise FileNotFoundError(
            f"Training dataset not found: {DATASET_PATH}. Run "
            "'python -m src.data_engineering.create_targets' first."
        )

    report = evaluate_walk_forward(pd.read_csv(DATASET_PATH))
    DEFAULT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("Project Alpha — expanding-window walk-forward evaluation")
    print(f"Folds per horizon: {report['n_splits']}")
    for horizon, result in report["horizons"].items():
        model = result["aggregate_model_metrics"]
        baseline = result["aggregate_zero_return_baseline"]
        improvement = result["aggregate_mae_improvement_pct"]
        print(
            f"{horizon}: folds_beating_zero={result['folds_beating_zero_baseline']}/"
            f"{report['n_splits']}, aggregate_MAE={model['mae']:.8f}, "
            f"zero_MAE={baseline['mae']:.8f}, "
            f"MAE_improvement={improvement:.2f}%"
            if improvement is not None
            else f"{horizon}: aggregate MAE={model['mae']:.8f}; baseline MAE is zero"
        )
    print(f"Report saved to: {DEFAULT_REPORT_PATH}")


if __name__ == "__main__":
    main()
