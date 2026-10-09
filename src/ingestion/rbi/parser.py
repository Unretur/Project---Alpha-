
import re
from pathlib import Path

import pandas as pd

from src.ingestion.rbi.loader import load_pdf_text


# --------------------------------------------------
# Paths
# --------------------------------------------------

RBI_DATA_DIR = Path("data/raw/rbi")

POLICY_PDF_PATH = RBI_DATA_DIR / (
    "Major Monetary Policy Rates and Reserve Requirements - "
    "Bank Rate, LAF (Repo, Reverse Repo, SDF and MSF) Rates, "
    "CRR & SLR.pdf"
)

EXCHANGE_PDF_PATH = RBI_DATA_DIR / (
    "Daily Exchange Rate of the Indian Rupee.pdf"
)

POLICY_OUTPUT_PATH = RBI_DATA_DIR / "policy_rates_parsed.csv"
EXCHANGE_OUTPUT_PATH = RBI_DATA_DIR / "exchange_rates_parsed.csv"


# --------------------------------------------------
# Policy rates
# --------------------------------------------------

POLICY_COLUMNS = [
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
        r"(\d{2}-\d{2}-\d{4})\s+(.+)"
    )

    for line in text.splitlines():
        match = pattern.match(line.strip())

        if not match:
            continue

        date_text = match.group(1)
        values = match.group(2).split()

        # Seven values are expected after the date.
        if len(values) != 7:
            continue

        rows.append([date_text] + values)

    df = pd.DataFrame(rows, columns=POLICY_COLUMNS)

    if df.empty:
        return df

    df["effective_date"] = pd.to_datetime(
        df["effective_date"],
        format="%d-%m-%Y",
        errors="coerce",
    )

    numeric_columns = POLICY_COLUMNS[1:]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    df = df.dropna(subset=["effective_date"])
    df = df.drop_duplicates(subset=["effective_date"])
    df = df.sort_values("effective_date").reset_index(drop=True)

    return df


# --------------------------------------------------
# Exchange rates
# --------------------------------------------------

def parse_exchange_rates(text: str) -> pd.DataFrame:
    rows = []

    pattern = re.compile(
        r"(\d{2}-[A-Za-z]{3}-\d{4})\s+"
        r"(\d+\.\d+)\s+"
        r"(\d+\.\d+)\s+"
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

    if df.empty:
        return df

    df["date"] = pd.to_datetime(
        df["date"],
        format="%d-%b-%Y",
        errors="coerce",
    )

    for column in ["usd_inr", "gbp_inr", "eur_inr"]:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    df = df.dropna(subset=["date"])
    df = df.drop_duplicates(subset=["date"])
    df = df.sort_values("date").reset_index(drop=True)

    return df


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():
    # Check the inputs before attempting to parse.
    required_files = [
        POLICY_PDF_PATH,
        EXCHANGE_PDF_PATH,
    ]

    missing_files = [
        path for path in required_files
        if not path.is_file()
    ]

    if missing_files:
        missing_list = "\n".join(
            f"  - {path}" for path in missing_files
        )
        raise FileNotFoundError(
            "Required RBI source PDF(s) are missing:\n"
            f"{missing_list}\n"
            "Restore these files before running the parser."
        )

    # Create the output directory.
    RBI_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------
    # Parse policy rates
    # ------------------------------

    print("Loading RBI policy-rate PDF...")
    policy_text = load_pdf_text(POLICY_PDF_PATH)

    policy_df = parse_policy_rates(policy_text)

    if policy_df.empty:
        raise ValueError(
            "No policy-rate rows were parsed. "
            "Inspect the PDF's extracted text and parsing pattern."
        )

    policy_df.to_csv(
        POLICY_OUTPUT_PATH,
        index=False,
    )

    print("Policy rates parsed successfully.")
    print("Rows:", len(policy_df))
    print("Missing values:")
    print(policy_df.isna().sum().to_string())
    print("Saved:", POLICY_OUTPUT_PATH)

    # ------------------------------
    # Parse exchange rates
    # ------------------------------

    print("\nLoading RBI exchange-rate PDF...")
    exchange_text = load_pdf_text(EXCHANGE_PDF_PATH)

    exchange_df = parse_exchange_rates(exchange_text)

    if exchange_df.empty:
        raise ValueError(
            "No exchange-rate rows were parsed. "
            "Inspect the PDF's extracted text and parsing pattern."
        )

    exchange_df.to_csv(
        EXCHANGE_OUTPUT_PATH,
        index=False,
    )

    print("\nExchange rates parsed successfully.")
    print("Rows:", len(exchange_df))
    print("Missing values:")
    print(exchange_df.isna().sum().to_string())
    print("Saved:", EXCHANGE_OUTPUT_PATH)


if __name__ == "__main__":
    main()
