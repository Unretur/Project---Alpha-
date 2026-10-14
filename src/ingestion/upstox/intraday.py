"""Fetch current-day NIFTY 50 five-minute candles and merge them safely.

Run from the repository root:
    python -m src.ingestion.upstox.intraday
This only refreshes market data; it does not generate signals or place orders.
"""
from pathlib import Path

import pandas as pd

from src.config.config import UPSTOX_ALGO_ACCESS_TOKEN
from src.ingestion.upstox.client import UpstoxClient

INSTRUMENT_KEY = "NSE_INDEX|Nifty 50"
INTERVAL = 5
OUTPUT_PATH = Path("data/raw/market/nifty50_5m.csv")
COLUMNS = [
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "open_interest",
]
NUMERIC_COLUMNS = ["open", "high", "low", "close", "volume", "open_interest"]


def _candles_to_frame(candles: list) -> pd.DataFrame:
    """Normalize Upstox candle arrays, allowing optional open-interest values."""
    rows = []
    for candle in candles:
        if not isinstance(candle, (list, tuple)) or len(candle) < 6:
            continue
        row = list(candle[:7])
        if len(row) == 6:
            row.append(None)
        rows.append(row)

    frame = pd.DataFrame(rows, columns=COLUMNS)
    if frame.empty:
        return frame

    frame["timestamp"] = pd.to_datetime(
        frame["timestamp"], utc=True, errors="coerce"
    )
    for column in NUMERIC_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    return frame.dropna(subset=["timestamp", "open", "high", "low", "close"])


def refresh_intraday(
    client: UpstoxClient,
    output_path: Path = OUTPUT_PATH,
) -> pd.DataFrame:
    """Fetch today's intraday candles, merge with existing history, and save."""
    encoded_key = "NSE_INDEX%7CNifty%2050"
    endpoint = f"/historical-candle/intraday/{encoded_key}/minutes/{INTERVAL}"

    print(f"Requesting current-day {INTERVAL}-minute candles for NIFTY 50...")
    response = client.get_v3(endpoint)
    candles = response.get("data", {}).get("candles", [])
    incoming = _candles_to_frame(candles)

    if incoming.empty:
        raise RuntimeError(
            "Upstox returned no valid intraday candles. The market may be closed, "
            "the endpoint may have returned no data, or the API request needs checking. "
            "Existing market data was left unchanged."
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        existing = pd.read_csv(output_path)
        if "timestamp" not in existing.columns:
            raise ValueError(f"Existing file has no timestamp column: {output_path}")
        existing["timestamp"] = pd.to_datetime(
            existing["timestamp"], utc=True, errors="coerce"
        )
        for column in COLUMNS:
            if column not in existing.columns:
                existing[column] = pd.NA
        existing = existing[COLUMNS]
        combined = pd.concat([existing, incoming[COLUMNS]], ignore_index=True)
    else:
        combined = incoming[COLUMNS].copy()

    combined["timestamp"] = pd.to_datetime(
        combined["timestamp"], utc=True, errors="coerce"
    )
    for column in NUMERIC_COLUMNS:
        combined[column] = pd.to_numeric(combined[column], errors="coerce")

    combined = combined.dropna(subset=["timestamp", "open", "high", "low", "close"])
    combined = (
        combined.drop_duplicates(subset=["timestamp"], keep="last")
        .sort_values("timestamp")
        .reset_index(drop=True)
    )
    combined.to_csv(output_path, index=False)

    print("\nIntraday refresh completed.")
    print("New candles received:", len(incoming))
    print("Total candles stored:", len(combined))
    print("Latest candle (UTC):", combined["timestamp"].max())
    print("Duplicate timestamps:", int(combined["timestamp"].duplicated().sum()))
    print("Chronologically sorted:", combined["timestamp"].is_monotonic_increasing)
    print("Saved to:", output_path)
    return combined


def main() -> None:
    if not UPSTOX_ALGO_ACCESS_TOKEN:
        raise ValueError(
            "UPSTOX_ALGO_ACCESS_TOKEN is missing. Check your local .env file."
        )
    refresh_intraday(UpstoxClient(UPSTOX_ALGO_ACCESS_TOKEN))


if __name__ == "__main__":
    main()
