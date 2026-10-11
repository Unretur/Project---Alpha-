"""Generate latest 5/15/30-minute return predictions from saved model artifacts.

By default, models must have beaten a zero-return MAE baseline on both
validation and the untouched test split. Use --allow-research-model only to
inspect experimental predictions that failed that deployment gate.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from src.models.baseline import DATASET_PATH, HORIZONS, build_feature_frame

ARTIFACT_DIR = Path("models/artifacts")


def predict_latest(
    dataset: pd.DataFrame,
    artifact_dir: Path = ARTIFACT_DIR,
    allow_research_model: bool = False,
) -> list[dict[str, Any]]:
    feature_frame, _ = build_feature_frame(dataset)
    feature_columns = [
        column
        for column in feature_frame.columns
        if column != "timestamp" and not column.startswith("target_")
    ]
    feature_frame[feature_columns] = feature_frame[feature_columns].replace(
        [np.inf, -np.inf], np.nan
    )
    usable = feature_frame.dropna(subset=feature_columns)
    if usable.empty:
        raise ValueError("No complete feature row is available for prediction.")
    latest = usable.iloc[[-1]]
    results: list[dict[str, Any]] = []

    for horizon in HORIZONS:
        artifact_path = artifact_dir / f"nifty_return_{horizon}m.joblib"
        if not artifact_path.is_file():
            raise FileNotFoundError(
                f"Missing model artifact: {artifact_path}. "
                "Run python -m src.models.train_model first."
            )
        artifact = joblib.load(artifact_path)
        if artifact.get("horizon_minutes") != horizon:
            raise ValueError(f"Artifact horizon mismatch: {artifact_path}")
        if not artifact.get("deployment_eligible", False) and not allow_research_model:
            raise RuntimeError(
                f"{horizon}m model failed the zero-return deployment gate. "
                "Do not use it for automated trading; pass --allow-research-model "
                "only for research inspection."
            )

        expected_features = artifact["feature_columns"]
        missing = set(expected_features).difference(latest.columns)
        if missing:
            raise ValueError(
                f"Latest data is missing trained features for {horizon}m: {sorted(missing)}"
            )
        row = latest[expected_features]
        if not np.isfinite(row.to_numpy(dtype=float)).all():
            raise ValueError(f"Latest feature row contains non-finite values for {horizon}m.")

        prediction = float(artifact["model"].predict(row)[0])
        results.append(
            {
                "timestamp": latest["timestamp"].iloc[0].isoformat(),
                "horizon_minutes": horizon,
                "predicted_forward_return": prediction,
                "model_name": artifact["model_name"],
                "deployment_eligible": bool(artifact.get("deployment_eligible", False)),
            }
        )
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DATASET_PATH)
    parser.add_argument("--artifact-dir", type=Path, default=ARTIFACT_DIR)
    parser.add_argument(
        "--allow-research-model",
        action="store_true",
        help="Print predictions from models that failed the benchmark gate; research only.",
    )
    args = parser.parse_args()

    if not args.dataset.is_file():
        raise FileNotFoundError(f"Prediction dataset not found: {args.dataset}")
    predictions = predict_latest(
        pd.read_csv(args.dataset),
        artifact_dir=args.artifact_dir,
        allow_research_model=args.allow_research_model,
    )
    print("Project Alpha — latest model predictions")
    for item in predictions:
        print(
            f"{item['horizon_minutes']}m | timestamp={item['timestamp']} | "
            f"predicted_return={item['predicted_forward_return']:.8f} | "
            f"model={item['model_name']} | "
            f"deployment_eligible={item['deployment_eligible']}"
        )


if __name__ == "__main__":
    main()
