"""Audit raw market and macro columns used by Project Alpha."""

import pandas as pd

from src.models.baseline import DATASET_PATH, MACRO_COLUMNS


def main() -> None:
    if not DATASET_PATH.is_file():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")

    data = pd.read_csv(DATASET_PATH)
    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True)

    columns_to_audit = [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "open_interest",
        *[column for column in MACRO_COLUMNS if column in data.columns],
    ]

    print("Project Alpha — Raw Data Audit")
    print(f"Dataset rows: {len(data)}")
    print(
        f"Timestamp range: {data['timestamp'].min()} to "
        f"{data['timestamp'].max()}"
    )

    for column in columns_to_audit:
        values = pd.to_numeric(data[column], errors="coerce")
        valid = values.dropna()

        print(f"\n{'=' * 55}")
        print(f"Column: {column}")
        print(f"Missing values: {values.isna().sum()}")
        print(f"Unique non-missing values: {valid.nunique()}")
        print(f"Minimum: {valid.min() if not valid.empty else 'N/A'}")
        print(f"Maximum: {valid.max() if not valid.empty else 'N/A'}")
        print(
            f"Standard deviation: "
            f"{valid.std() if len(valid) > 1 else 'N/A'}"
        )

        if column in MACRO_COLUMNS and not valid.empty:
            print("First 5 distinct values:")
            print(valid.drop_duplicates().head(5).to_string(index=False))

    print("\nAudit completed. No files were modified.")


if __name__ == "__main__":
    main()
