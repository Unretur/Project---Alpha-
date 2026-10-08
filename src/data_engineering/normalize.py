from __future__ import annotations

from pathlib import Path

import pandas as pd


def normalize_datetime(
    df: pd.DataFrame,
    column: str,
) -> pd.DataFrame:
    """
    Normalize a datetime column to timezone-aware UTC timestamps.
    """

    result = df.copy()

    result[column] = pd.to_datetime(
        result[column],
        utc=True,
        errors="coerce",
    )

    return result


def sort_by_datetime(
    df: pd.DataFrame,
    column: str,
) -> pd.DataFrame:
    """
    Sort a DataFrame chronologically by its datetime column.
    """

    result = df.copy()

    result = result.sort_values(
        by=column
    ).reset_index(drop=True)

    return result


def remove_duplicate_timestamps(
    df: pd.DataFrame,
    column: str,
) -> pd.DataFrame:
    """
    Remove duplicate timestamps while keeping the first observation.
    """

    result = df.copy()

    result = result.drop_duplicates(
        subset=[column],
        keep="first",
    ).reset_index(drop=True)

    return result


if __name__ == "__main__":
    input_path = Path(
        "data/raw/market/nifty50_5m.csv"
    )

    df = pd.read_csv(input_path)

    print("Original shape:", df.shape)
    print()
    print("Original columns:")
    print(df.columns.tolist())
    print()

    df = normalize_datetime(
        df,
        "timestamp",
    )

    df = sort_by_datetime(
        df,
        "timestamp",
    )

    df = remove_duplicate_timestamps(
        df,
        "timestamp",
    )

    print("Normalized shape:", df.shape)
    print()

    print("Dtypes:")
    print(df.dtypes)
    print()

    print("First 5 rows:")
    print(df.head())
    print()

    print("Last 5 rows:")
    print(df.tail())
    print()

    print(
        "Duplicate timestamps:",
        df["timestamp"].duplicated().sum(),
    )

    print(
        "Missing timestamps:",
        df["timestamp"].isna().sum(),
    )