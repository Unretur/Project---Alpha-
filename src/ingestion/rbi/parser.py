import re
from pathlib import Path

import pandas as pd

from src.ingestion.rbi.loader import load_pdf_text


COLUMNS = [
    "effective_date",
    "bank_rate",
    "repo_rate",
    "reverse_repo_rate",
    "sdf_rate",
    "msf_rate",
    "crr",
    "slr",
]


def parse_policy_rates(text: str) -> pd.DataFrame:
    rows = []

    pattern = re.compile(
        r"(\d{2}-\d{2}-\d{4})"
        r"\s+"
        r"(.+)"
    )

    for line in text.splitlines():
        match = pattern.match(line.strip())

        if not match:
            continue

        date = match.group(1)
        values = match.group(2).split()

        if len(values) != 7:
            continue

        rows.append([date] + values)

    df = pd.DataFrame(rows, columns=COLUMNS)

    df["effective_date"] = pd.to_datetime(
        df["effective_date"],
        format="%d-%m-%Y",
    )

    numeric_columns = COLUMNS[1:]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    return df


def parse_exchange_rates(text: str) -> pd.DataFrame:
    rows = []

    pattern = re.compile(
        r"(\d{2}-[A-Za-z]{3}-\d{4})"
        r"\s+"
        r"(\d+\.\d+)"
        r"\s+"
        r"(\d+\.\d+)"
        r"\s+"
        r"(\d+\.\d+)"
    )

    for line in text.splitlines():
        match = pattern.match(line.strip())

        if not match:
            continue

        rows.append(match.groups())

    df = pd.DataFrame(
        rows,
        columns=[
            "date",
            "usd_inr",
            "gbp_inr",
            "eur_inr",
        ],
    )

    df["date"] = pd.to_datetime(
        df["date"],
        format="%d-%b-%Y",
    )

    numeric_columns = [
        "usd_inr",
        "gbp_inr",
        "eur_inr",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    return df


if __name__ == "__main__":

    # -----------------------------
    # Policy rates
    # -----------------------------

    policy_pdf_path = Path(
    "data/raw/rbi/"
    "Major Monetary Policy Rates and Reserve Requirements - "
    "Bank Rate, LAF (Repo, Reverse Repo, SDF and MSF) Rates, "
    "CRR & SLR.pdf"
)

    policy_text = load_pdf_text(policy_pdf_path)

    policy_df = parse_policy_rates(policy_text)

    print(policy_df.head(10))
    print()
    print("Rows:", len(policy_df))
    print()
    print(policy_df.dtypes)

    policy_output_path = Path(
        "data/raw/rbi/policy_rates_parsed.csv"
    )

    policy_df.to_csv(
        policy_output_path,
        index=False,
    )

    print()
    print("Saved:", policy_output_path)


    # -----------------------------
    # Exchange rates
    # -----------------------------

    exchange_pdf_path = Path(
        "data/raw/rbi/"
        "Daily Exchange Rate of the Indian Rupee.pdf"
    )

    exchange_text = load_pdf_text(exchange_pdf_path)

    exchange_df = parse_exchange_rates(exchange_text)

    print()
    print("Exchange rates parsed successfully")
    print(exchange_df.head(10))
    print()
    print("Rows:", len(exchange_df))
    print()
    print(exchange_df.dtypes)

    exchange_output_path = Path(
        "data/raw/rbi/exchange_rates_parsed.csv"
    )

    exchange_df.to_csv(
        exchange_output_path,
        index=False,
    )

    print()
    print("Saved:", exchange_output_path)