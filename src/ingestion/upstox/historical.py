
from calendar import monthrange
from datetime import date
from pathlib import Path

import pandas as pd

from src.config.config import UPSTOX_ALGO_ACCESS_TOKEN
from src.ingestion.upstox.client import UpstoxClient

INSTRUMENT_KEY = "NSE_INDEX|Nifty 50"
INTERVAL = 5

FROM_DATE = date(2026, 1, 1)
TO_DATE = date(2026, 10, 8)

OUTPUT_PATH = Path("data/raw/market/nifty50_5m.csv")


def main():
    if not UPSTOX_ALGO_ACCESS_TOKEN:
        raise ValueError(
            "UPSTOX_ALGO_ACCESS_TOKEN is missing. Check your .env file."
        )

    client = UpstoxClient(UPSTOX_ALGO_ACCESS_TOKEN)
    all_candles = []

    # Download one calendar month per API request.
    current = FROM_DATE.replace(day=1)

    while current <= TO_DATE:
        month_end_day = monthrange(current.year, current.month)[1]
        chunk_end = min(
            date(current.year, current.month, month_end_day),
            TO_DATE,
        )

        # Skip dates outside the requested overall range.
        chunk_start = max(current, FROM_DATE)

        endpoint = (
            "/historical-candle/"
            f"{INSTRUMENT_KEY.replace('|', '%7C')}/"
            f"minutes/{INTERVAL}/"
            f"{chunk_end.isoformat()}/"
            f"{chunk_start.isoformat()}"
        )

        print(f"Downloading {chunk_start} to {chunk_end}...")

        response = client.get_v3(endpoint)
        candles = response.get("data", {}).get("candles", [])

        print(f"  Candles received: {len(candles)}")
        all_candles.extend(candles)

        # Move to the next month.
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)

    if not all_candles:
        raise ValueError("No historical candles were returned by Upstox.")

    columns = [
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "open_interest",
    ]

    df = pd.DataFrame(all_candles, columns=columns)

    df["timestamp"] = pd.to_datetime(
        df["timestamp"], utc=True, errors="coerce"
    )
    df = df.dropna(subset=["timestamp"])
    df = df.drop_duplicates(subset=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)

    print("\nHistorical download completed.")
    print("Total candles:", len(df))
    print("First timestamp:", df["timestamp"].min())
    print("Last timestamp:", df["timestamp"].max())
    print("Duplicate timestamps:", df["timestamp"].duplicated().sum())
    print("Chronologically sorted:", df["timestamp"].is_monotonic_increasing)
    print("Saved to:", OUTPUT_PATH)


if __name__ == "__main__":
    main()

