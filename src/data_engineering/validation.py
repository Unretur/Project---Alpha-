from __future__ import annotations

import pandas as pd


def validate_datetime_column(
    df: pd.DataFrame,
    column: str,
) -> None:
    if column not in df.columns:
        raise ValueError(
            f"Missing datetime column: {column}"
        )

    if not pd.api.types.is_datetime64_any_dtype(
        df[column]
    ):
        raise TypeError(
            f"{column} must be a datetime column"
        )

    if df[column].isna().any():
        raise ValueError(
            f"{column} contains missing timestamps"
        )


def validate_sorted(
    df: pd.DataFrame,
    column: str,
) -> None:
    if not df[column].is_monotonic_increasing:
        raise ValueError(
            f"{column} is not sorted chronologically"
        )


def validate_no_duplicates(
    df: pd.DataFrame,
    column: str,
) -> None:
    duplicates = df[column].duplicated().sum()

    if duplicates > 0:
        raise ValueError(
            f"{duplicates} duplicate timestamps found "
            f"in {column}"
        )


def validate_no_lookahead(
    df: pd.DataFrame,
    decision_column: str,
    available_column: str,
) -> None:
    violations = (
        df[available_column]
        > df[decision_column]
    ).sum()

    if violations > 0:
        raise ValueError(
            f"{violations} look-ahead violations detected"
        )


if __name__ == "__main__":

    test_df = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                [
                    "2026-10-05 10:00:00",
                    "2026-10-05 10:05:00",
                    "2026-10-05 10:10:00",
                ],
                utc=True,
            )
        }
    )

    validate_datetime_column(
        test_df,
        "timestamp",
    )

    validate_sorted(
        test_df,
        "timestamp",
    )

    validate_no_duplicates(
        test_df,
        "timestamp",
    )

    print("All validation tests passed.")