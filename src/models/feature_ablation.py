"""Compare price-action and macro feature groups with walk-forward evaluation.

This is exploratory ablation analysis. It must not be used to select a final
model from the same folds and then report those folds as an unbiased test.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.models.baseline import DATASET_PATH, build_feature_frame
from src.models.walk_forward_evaluation import evaluate_walk_forward

REPORT_PATH = Path("data/processed/feature_ablation_metrics.json")
MACRO_PREFIXES = ("vix_", "us10y_", "fed_funds_", "usd_inr_fred_")


def evaluate_feature_groups(dataset: pd.DataFrame) -> dict[str, Any]:
    _, features = build_feature_frame(dataset)
    price_features = [
        name for name in features
        if name.startswith(("close_return_", "candle_"))
    ]
    macro_features = [
        name for name in features if name.startswith(MACRO_PREFIXES)
    ]
    groups = {
        "price_action_only": price_features,
        "macro_only": macro_features,
        "price_action_plus_macro": price_features + macro_features,
    }
    empty_groups = [name for name, columns in groups.items() if not columns]
    if empty_groups:
        raise ValueError(
            f"Cannot evaluate empty feature groups: {empty_groups}. "
            f"Available features: {features}"
        )

    return {
        "purpose": (
            "Exploratory feature-group ablation; results are not an unbiased "
            "final model-selection estimate."
        ),
        "method": "expanding_window_walk_forward",
        "feature_groups": {
            name: {
                "feature_count": len(columns),
                "features": columns,
                "evaluation": evaluate_walk_forward(
                    dataset, selected_features=columns
                ),
            }
            for name, columns in groups.items()
        },
        "interpretation_notes": [
            "Compare the same folds across groups; do not treat fold results as independent.",
            "A better feature-group result is evidence for further investigation, not proof of tradable profitability.",
            "The macro data still uses conservative availability proxies rather than exact release vintages.",
            "No transaction costs, slippage, or order execution are simulated.",
        ],
    }


def main() -> None:
    if not DATASET_PATH.is_file():
        raise FileNotFoundError(
            f"Training dataset not found: {DATASET_PATH}. Run "
            "'python -m src.data_engineering.create_targets' first."
        )
    report = evaluate_feature_groups(pd.read_csv(DATASET_PATH))
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("Project Alpha — walk-forward feature-group ablation")
    for group_name, group in report["feature_groups"].items():
        print(f"\n{group_name} ({group['feature_count']} features)")
        for horizon, metrics in group["evaluation"]["horizons"].items():
            model = metrics["aggregate_model_metrics"]
            baseline = metrics["aggregate_zero_return_baseline"]
            improvement = metrics["aggregate_mae_improvement_pct"]
            print(
                f"  {horizon}: folds_beating_zero="
                f"{metrics['folds_beating_zero_baseline']}/"
                f"{group['evaluation']['n_splits']}, "
                f"MAE={model['mae']:.8f}, zero_MAE={baseline['mae']:.8f}, "
                f"improvement={improvement:.2f}%"
            )
    print(f"\nReport saved to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
