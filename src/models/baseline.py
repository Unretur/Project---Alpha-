"""Leakage-conscious Ridge baselines for NIFTY forward returns.

Run from the repository root:
    python -m src.models.baseline

Predictors are lagged at least one candle. Splits are chronological, and
training/validation rows are purged by the maximum target horizon so labels do
not reach into the following split. Results are research metrics, not a trading
performance claim.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

DATASET_PATH = Path("data/processed/nifty_training_dataset.csv")
METRICS_PATH = Path("data/processed/baseline_metrics.json")
HORIZONS = (5, 15, 30)
MACRO_COLUMNS = ("vix", "us10y", "fed_funds", "usd_inr_fred")
MAX_HORIZON = max(HORIZONS)


def build_feature_frame(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Build predictors using information no later than the prior candle."""
    required = {
        "timestamp", "open", "high", "low", "close", "volume", "open_interest",
        *(f"target_return_{h}m" for h in HORIZONS),
    }
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Dataset is missing required columns: {sorted(missing)}")

    data = frame.copy()
    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True, errors="raise")
    data = data.sort_values("timestamp").reset_index(drop=True)
    if data["timestamp"].isna().any() or data["timestamp"].duplicated().any():
        raise ValueError("Dataset timestamps must be non-null and unique.")

    for column in ("open", "high", "low", "close", "volume", "open_interest"):
        data[column] = pd.to_numeric(data[column], errors="raise")
    if (data["close"] <= 0).any() or (data["open"] <= 0).any():
        raise ValueError("Open and close prices must be positive.")
    if (data["volume"] < 0).any():
        raise ValueError("Volume cannot be negative.")

    features = pd.DataFrame(index=data.index)
    close = data["close"]
    for lag in (1, 3, 6, 12):
        features[f"close_return_lag_{lag}"] = close.pct_change(
            periods=lag, fill_method=None
        ).shift(1)

    features["candle_range_lag_1"] = (
        (data["high"] - data["low"]) / close
    ).shift(1)
    features["candle_body_lag_1"] = (
        (data["close"] - data["open"]) / data["open"]
    ).shift(1)
    features["log_volume_change_lag_1"] = np.log1p(
        data["volume"]
    ).diff().shift(1)
    features["open_interest_change_lag_1"] = data[
        "open_interest"
    ].pct_change(fill_method=None).shift(1)

    for column in MACRO_COLUMNS:
        if column in data.columns:
            values = pd.to_numeric(data[column], errors="raise")
            features[f"{column}_lag_1"] = values.shift(1)
            features[f"{column}_change_lag_1"] = values.diff().shift(1)

    targets = data[[f"target_return_{h}m" for h in HORIZONS]].apply(
        pd.to_numeric, errors="raise"
    )
    result = pd.concat([data[["timestamp"]], features, targets], axis=1)
    feature_columns = list(features.columns)
    if not feature_columns:
        raise ValueError("No model features were constructed.")
    if any(
        column.startswith("target_") or column.endswith("_available_time")
        for column in feature_columns
    ):
        raise ValueError("Target or availability metadata leaked into features.")
    return result, feature_columns


def chronological_split(
    data: pd.DataFrame,
    train_fraction: float = 0.70,
    validation_fraction: float = 0.15,
    max_horizon_minutes: int = MAX_HORIZON,
) -> dict[str, pd.DataFrame]:
    """Split by time and purge labels whose forward horizon crosses a split."""
    if not 0 < train_fraction < 1:
        raise ValueError("train_fraction must be between 0 and 1.")
    if not 0 < validation_fraction < 1 or train_fraction + validation_fraction >= 1:
        raise ValueError("Fractions must be positive and leave a test segment.")
    if max_horizon_minutes <= 0:
        raise ValueError("max_horizon_minutes must be positive.")

    ordered = data.sort_values("timestamp").reset_index(drop=True)
    n = len(ordered)
    train_end = int(n * train_fraction)
    validation_end = int(n * (train_fraction + validation_fraction))
    if train_end < 1 or validation_end <= train_end or validation_end >= n:
        raise ValueError("Not enough rows for chronological train/validation/test splits.")

    validation_start = ordered.loc[train_end, "timestamp"]
    test_start = ordered.loc[validation_end, "timestamp"]
    horizon = pd.Timedelta(minutes=max_horizon_minutes)

    train = ordered.iloc[:train_end].copy()
    validation = ordered.iloc[train_end:validation_end].copy()
    test = ordered.iloc[validation_end:].copy()
    train = train.loc[train["timestamp"] + horizon < validation_start]
    validation = validation.loc[validation["timestamp"] + horizon < test_start]
    return {"train": train, "validation": validation, "test": test}


def _metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float | int]:
    return {
        "rows": int(len(y_true)),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "directional_accuracy": float(np.mean(np.sign(y_true) == np.sign(y_pred))),
    }


def run_baselines(dataset: pd.DataFrame) -> dict:
    """Train/evaluate one Ridge regression baseline per return horizon."""
    feature_frame, feature_columns = build_feature_frame(dataset)
    splits = chronological_split(feature_frame)
    results: dict = {
        "model": "StandardScaler + Ridge(alpha=1.0)",
        "feature_count": len(feature_columns),
        "features": feature_columns,
        "splits": {},
        "horizons": {},
        "limitations": [
            "Research baseline only; not a trading strategy or profitability claim.",
            "Macro availability timestamps are conservative proxies, not exact release vintages.",
            "Historical point-in-time news features are not included.",
        ],
    }

    for split_name, split_frame in splits.items():
        results["splits"][split_name] = {
            "rows_before_target_filter": int(len(split_frame)),
            "start": split_frame["timestamp"].min().isoformat() if len(split_frame) else None,
            "end": split_frame["timestamp"].max().isoformat() if len(split_frame) else None,
        }

    for horizon in HORIZONS:
        target = f"target_return_{horizon}m"
        usable_train = splits["train"].dropna(subset=feature_columns + [target])
        usable_validation = splits["validation"].dropna(subset=feature_columns + [target])
        usable_test = splits["test"].dropna(subset=feature_columns + [target])
        if min(len(usable_train), len(usable_validation), len(usable_test)) == 0:
            raise ValueError(
                f"Insufficient usable rows for {target}: train={len(usable_train)}, "
                f"validation={len(usable_validation)}, test={len(usable_test)}"
            )

        model = make_pipeline(StandardScaler(), Ridge(alpha=1.0))
        model.fit(usable_train[feature_columns], usable_train[target])
        validation_prediction = model.predict(usable_validation[feature_columns])
        test_prediction = model.predict(usable_test[feature_columns])
        test_actual = usable_test[target].to_numpy()
        zero_prediction = np.zeros_like(test_actual)

        results["horizons"][f"{horizon}m"] = {
            "train_rows": int(len(usable_train)),
            "validation_rows": int(len(usable_validation)),
            "test_rows": int(len(usable_test)),
            "validation": _metrics(
                usable_validation[target].to_numpy(), validation_prediction
            ),
            "test": _metrics(test_actual, test_prediction),
            "zero_return_baseline_test": _metrics(test_actual, zero_prediction),
        }
    return results


def main() -> None:
    if not DATASET_PATH.is_file():
        raise FileNotFoundError(
            f"Training dataset not found: {DATASET_PATH}. "
            "Run python -m src.data_engineering.create_targets first."
        )
    results = run_baselines(pd.read_csv(DATASET_PATH))
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    METRICS_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("Baseline training and chronological evaluation completed.")
    print(f"Feature count: {results['feature_count']}")
    for horizon, metrics in results["horizons"].items():
        test = metrics["test"]
        zero = metrics["zero_return_baseline_test"]
        print(
            f"{horizon}: train={metrics['train_rows']}, "
            f"validation={metrics['validation_rows']}, test={metrics['test_rows']}, "
            f"test MAE={test['mae']:.8f}, test RMSE={test['rmse']:.8f}, "
            f"directional accuracy={test['directional_accuracy']:.3f}, "
            f"zero-baseline MAE={zero['mae']:.8f}"
        )
    print(f"Metrics saved to: {METRICS_PATH}")


if __name__ == "__main__":
    main()
