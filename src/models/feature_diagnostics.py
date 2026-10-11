
"""Inspect feature quality and relationships with future returns."""

import numpy as np
import pandas as pd

from src.models.baseline import (
    DATASET_PATH,
    HORIZONS,
    build_feature_frame,
    chronological_split,
)


def main() -> None:
    if not DATASET_PATH.is_file():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")

    dataset = pd.read_csv(DATASET_PATH)
    feature_frame, feature_columns = build_feature_frame(dataset)
    splits = chronological_split(feature_frame)

    print("Project Alpha — Feature diagnostics")
    print(f"Dataset rows: {len(dataset)}")
    print(f"Feature count: {len(feature_columns)}")

    # 1. Check missingness and variability across the full feature dataset.
    print("\n" + "=" * 65)
    print("1. FEATURE QUALITY")

    quality_rows = []

    for column in feature_columns:
        values = pd.to_numeric(feature_frame[column], errors="coerce")
        quality_rows.append(
            {
                "feature": column,
                "missing_pct": values.isna().mean() * 100,
                "unique_values": values.nunique(dropna=True),
                "std": values.std(),
            }
        )

    quality = pd.DataFrame(quality_rows)
    print(
        quality.sort_values("missing_pct", ascending=False).to_string(
            index=False,
            formatters={
                "missing_pct": "{:.2f}%".format,
                "std": lambda value: (
                    f"{value:.8g}" if pd.notna(value) else "NaN"
                ),
            },
        )
    )

    # 2. Check feature-to-target Pearson correlations.
    print("\n" + "=" * 65)
    print("2. FEATURE-TO-TARGET CORRELATIONS")
    print("Pearson correlation measures linear association, not causation.")

    for horizon in HORIZONS:
        target = f"target_return_{horizon}m"
        usable = feature_frame.dropna(subset=feature_columns + [target])

        if usable.empty:
            print(f"\n{target}: no complete rows; skipped.")
            continue

        correlations = (
            usable[feature_columns]
            .corrwith(usable[target])
            .dropna()
            .sort_values(key=lambda values: values.abs(), ascending=False)
        )

        print(f"\n{target} — complete rows: {len(usable)}")
        print(correlations.head(10).to_string(float_format=lambda value: f"{value:.5f}"))

    # 3. Compare feature distributions between chronological train and test.
    print("\n" + "=" * 65)
    print("3. TRAIN/TEST FEATURE DISTRIBUTION CHECK")

    train = splits["train"]
    test = splits["test"]

    distribution_rows = []

    for column in feature_columns:
        train_values = train[column].dropna()
        test_values = test[column].dropna()

        train_mean = train_values.mean() if len(train_values) else np.nan
        test_mean = test_values.mean() if len(test_values) else np.nan
        train_std = train_values.std() if len(train_values) else np.nan
        test_std = test_values.std() if len(test_values) else np.nan

        if pd.notna(train_std) and train_std > 0 and pd.notna(test_mean):
            mean_shift_in_train_std = (test_mean - train_mean) / train_std
        else:
            mean_shift_in_train_std = np.nan

        if pd.notna(train_std) and train_std > 0:
            std_ratio = test_std / train_std
        else:
            std_ratio = np.nan

        distribution_rows.append(
            {
                "feature": column,
                "train_mean": train_mean,
                "test_mean": test_mean,
                "mean_shift_train_std": mean_shift_in_train_std,
                "test_to_train_std_ratio": std_ratio,
            }
        )

    distribution = pd.DataFrame(distribution_rows)
    print(
        distribution.to_string(
            index=False,
            formatters={
                "train_mean": lambda value: f"{value:.6g}" if pd.notna(value) else "NaN",
                "test_mean": lambda value: f"{value:.6g}" if pd.notna(value) else "NaN",
                "mean_shift_train_std": lambda value: f"{value:.3f}" if pd.notna(value) else "NaN",
                "test_to_train_std_ratio": lambda value: f"{value:.3f}" if pd.notna(value) else "NaN",
            },
        )
    )

    print("\nDiagnostics completed. No dataset or model files were modified.")


if __name__ == "__main__":
    main()
