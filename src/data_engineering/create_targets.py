"""Create leakage-safe forward-return targets for Project Alpha.

The input uses 5-minute candle timestamps. A target is only assigned when the
exact future timestamp exists; gaps, overnight boundaries, and missing candles
therefore produce NaN targets rather than silently using a later row.
"""
from pathlib import Path

import pandas as pd

INPUT_PATH = Path("data/processed/nifty_macro_aligned.csv")
OUTPUT_PATH = Path("data/processed/nifty_training_dataset.csv")
HORIZONS_MINUTES = (5, 15, 30)


def add_forward_return_targets(
    frame: pd.DataFrame,
    timestamp_column: str = "timestamp",
    close_column: str = "close",
    horizons_minutes: tuple[int, ...] = HORIZONS_MINUTES,
) -> pd.DataFrame:
    """Add forward returns and direction labels at exact elapsed-time horizons."""
    required = {timestamp_column, close_column}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Input is missing required columns: {sorted(missing)}")

    if not horizons_minutes or any(h <= 0 or h % 5 for h in horizons_minutes):
        raise ValueError("Horizons must be positive multiples of the 5-minute candle interval.")

    result = frame.copy()
    result[timestamp_column] = pd.to_datetime(
        result[timestamp_column], utc=True, errors="raise"
    )
    result = result.sort_values(timestamp_column).reset_index(drop=True)

    if result[timestamp_column].duplicated().any():
        raise ValueError(f"{timestamp_column} must contain unique timestamps.")

    result[close_column] = pd.to_numeric(result[close_column], errors="raise")
    if result[close_column].isna().any() or (result[close_column] <= 0).any():
        raise ValueError(f"{close_column} must contain positive, non-null prices.")

    # A timestamp lookup prevents a row shift from accidentally crossing a
    # missing candle or a market-session gap.
    future_lookup = result[[timestamp_column, close_column]].rename(
        columns={
            timestamp_column: "_future_timestamp",
            close_column: "_future_close",
        }
    )

    for horizon in horizons_minutes:
        target_timestamp = result[timestamp_column] + pd.Timedelta(minutes=horizon)
        lookup = pd.DataFrame(
            {
                timestamp_column: result[timestamp_column],
                "_future_timestamp": target_timestamp,
            }
        )
        lookup = lookup.merge(
            future_lookup,
            on="_future_timestamp",
            how="left",
            validate="one_to_one",
        )
        returns = lookup["_future_close"].div(result[close_column]).sub(1.0)
        result[f"target_return_{horizon}m"] = returns
        result[f"target_direction_{horizon}m"] = returns.map(
            lambda value: "up" if value > 0 else ("down" if value < 0 else "flat")
            if pd.notna(value)
            else pd.NA
        )

    return result


def main() -> None:
    if not INPUT_PATH.is_file():
        raise FileNotFoundError(
            f"Aligned input not found: {INPUT_PATH}. Run "
            "'python -m src.data_engineering.build_aligned_dataset' first."
        )

    aligned = pd.read_csv(INPUT_PATH)
    dataset = add_forward_return_targets(aligned)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(OUTPUT_PATH, index=False)

    print("Forward-return target generation completed.")
    print(f"Input rows: {len(aligned)}")
    print(f"Output rows: {len(dataset)}")
    for horizon in HORIZONS_MINUTES:
        column = f"target_return_{horizon}m"
        print(
            f"{horizon}-minute targets: {dataset[column].notna().sum()} valid, "
            f"{dataset[column].isna().sum()} unavailable"
        )
    print(f"Saved: {OUTPUT_PATH}")
    print(
        "Note: *_available_time columns are metadata, not model features. "
        "News features are excluded until point-in-time historical news is available."
    )


if __name__ == "__main__":
    main()
