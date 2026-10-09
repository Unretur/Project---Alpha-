from pathlib import Path

from src.ingestion.fred.download_series import download_fred_series


SERIES = {
    "VIXCLS": "VIXCLS.csv",
    "DGS10": "DGS10.csv",
    "DFF": "DFF.csv",
    "DEXINUS": "DEXINUS.csv",
}


if __name__ == "__main__":

    output_directory = Path(
        "data/raw/fred"
    )

    for series_id, filename in SERIES.items():

        output_path = output_directory / filename

        df = download_fred_series(
            series_id=series_id,
            output_path=output_path,
        )

        print()
        print(
            f"{series_id} downloaded successfully"
        )
        print("Rows:", len(df))
        print("Latest observation:")
        print(df.tail(1))
        print("Saved:", output_path)