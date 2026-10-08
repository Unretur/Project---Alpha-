from pathlib import Path

import pandas as pd

from src.data_engineering.normalize import (
    normalize_datetime,
    sort_by_datetime,
    remove_duplicate_timestamps,
)

from src.data_engineering.time_alignment import align_asof


if __name__ == "__main__":

    # -----------------------------
    # Load NIFTY 5-minute data
    # -----------------------------

    nifty_path = Path(
        "data/raw/market/nifty50_5m.csv"
    )

    nifty = pd.read_csv(nifty_path)

    nifty = normalize_datetime(
        nifty,
        "timestamp",
    )

    nifty = sort_by_datetime(
        nifty,
        "timestamp",
    )

    nifty = remove_duplicate_timestamps(
        nifty,
        "timestamp",
    )

    # -----------------------------
    # Load VIX data
    # -----------------------------

    vix_path = Path(
        "data/raw/fred/VIXCLS.csv"
    )

    vix = pd.read_csv(vix_path)

    vix = normalize_datetime(
        vix,
        "date",
    )

    vix = sort_by_datetime(
        vix,
        "date",
    )

    vix = remove_duplicate_timestamps(
        vix,
        "date",
    )

    # Rename VIX timestamp to make the meaning explicit.
    vix = vix.rename(
        columns={
            "date": "vix_available_time",
            "value": "vix",
        }
    )

    # -----------------------------
    # Align VIX to NIFTY
    # -----------------------------

    aligned = align_asof(
        nifty,
        vix,
        left_on="timestamp",
        right_on="vix_available_time",
    )

    # -----------------------------
    # Validation
    # -----------------------------

    print("NIFTY rows:", len(nifty))
    print("VIX rows:", len(vix))
    print("Aligned rows:", len(aligned))
    print()

    print("Aligned columns:")
    print(aligned.columns.tolist())
    print()

    print("First 10 aligned rows:")
    print(
        aligned[
            [
                "timestamp",
                "close",
                "vix_available_time",
                "vix",
            ]
        ].head(10)
    )
    print()

    print("Last 10 aligned rows:")
    print(
        aligned[
            [
                "timestamp",
                "close",
                "vix_available_time",
                "vix",
            ]
        ].tail(10)
    )
    print()

    # Check for look-ahead.
    lookahead_count = (
        aligned["vix_available_time"]
        > aligned["timestamp"]
    ).sum()

    print(
        "Look-ahead violations:",
        lookahead_count,
    )

    print()

    # Check how many NIFTY rows have a VIX value.
    missing_vix = aligned["vix"].isna().sum()

    print(
        "Rows with missing VIX:",
        missing_vix,
    )