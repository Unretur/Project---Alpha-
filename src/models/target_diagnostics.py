
"""Inspect target-return distributions for Project Alpha."""

from pathlib import Path

import pandas as pd


DATASET_PATH = Path("data/processed/nifty_training_dataset.csv")
HORIZONS = (5, 15, 30)


def main():
    if not DATASET_PATH.is_file():
        raise FileNotFoundError(
            f"Dataset not found: {DATASET_PATH}"
        )

    data = pd.read_csv(DATASET_PATH)

    print(f"Dataset rows: {len(data)}")
    print(f"Dataset columns: {len(data.columns)}")

    for horizon in HORIZONS:
        column = f"target_return_{horizon}m"

        print(f"\n{'=' * 50}")
        print(f"Target: {column}")

        if column not in data.columns:
            print(f"Missing target column: {column}")
            continue

        target = pd.to_numeric(data[column], errors="coerce")
        valid = target.dropna()

        print(f"Total rows: {len(target)}")
        print(f"Valid rows: {len(valid)}")
        print(f"Missing rows: {target.isna().sum()}")

        if valid.empty:
            print("No valid target values to analyse.")
            continue

        print(f"Mean return: {valid.mean():.8f}")
        print(f"Standard deviation: {valid.std():.8f}")
        print(f"Minimum return: {valid.min():.8f}")
        print(f"Maximum return: {valid.max():.8f}")

        print(f"Positive returns: {(valid > 0).mean() * 100:.2f}%")
        print(f"Negative returns: {(valid < 0).mean() * 100:.2f}%")
        print(f"Zero returns: {(valid == 0).mean() * 100:.2f}%")


if __name__ == "__main__":
    main()
