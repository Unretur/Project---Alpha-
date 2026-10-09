from datetime import date
import os
from pathlib import Path

import pandas as pd

from src.config.config import FRED_API_KEY
from src.ingestion.fred.client import client


def download_fred_series(
    series_id: str,
    output_path: Path,
) -> pd.DataFrame:

    if not FRED_API_KEY:
        raise ValueError(
            "FRED_API_KEY is missing. Set it in your .env file."
        )

    response = client.get(
        "/series/observations",
        params={
            "series_id": series_id,
            "observation_start": os.getenv("FRED_OBSERVATION_START", "2020-01-01"),
            "observation_end": os.getenv(
                "FRED_OBSERVATION_END", date.today().isoformat()
            ),
        },
    )

    observations = response["observations"]

    df = pd.DataFrame(observations)

    df = df[
        ["date", "value"]
    ].copy()

    df["date"] = pd.to_datetime(
        df["date"],
        utc=True,
    )

    df["value"] = pd.to_numeric(
        df["value"],
        errors="coerce",
    )

    df = df.dropna(
        subset=["value"]
    )

    df = df.sort_values(
        "date"
    ).reset_index(drop=True)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(
        output_path,
        index=False,
    )

    return df


if __name__ == "__main__":

    output_path = Path(
        "data/raw/fred/VIXCLS.csv"
    )

    df = download_fred_series(
        series_id="VIXCLS",
        output_path=output_path,
    )

    print("FRED series downloaded successfully")
    print()
    print("Rows:", len(df))
    print()
    print(df.head())
    print()
    print(df.tail())
    print()
    print("Dtypes:")
    print(df.dtypes)
    print()
    print("Saved:", output_path)