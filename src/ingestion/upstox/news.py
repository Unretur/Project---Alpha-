
from pathlib import Path

import pandas as pd
import requests

from src.config.config import UPSTOX_ALGO_ACCESS_TOKEN


BASE_URL = "https://api.upstox.com/v2/news"

OUTPUT_PATH = Path("data/raw/news/upstox_news.csv")

# Reliance Industries, a NIFTY 50 constituent.
INSTRUMENT_KEYS = ["NSE_EQ|INE002A01018"]


def fetch_news(
    instrument_keys: list[str],
    page_number: int = 1,
    page_size: int = 20,
) -> list[dict]:

    if not UPSTOX_ALGO_ACCESS_TOKEN:
        raise RuntimeError(
            "UPSTOX_ALGO_ACCESS_TOKEN is missing."
        )

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {UPSTOX_ALGO_ACCESS_TOKEN}",
    }

    params = {
        "category": "instrument_keys",
        "instrument_keys": ",".join(instrument_keys),
        "page_number": page_number,
        "page_size": page_size,
    }

    response = requests.get(
        BASE_URL,
        headers=headers,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    payload = response.json()

    if payload.get("status") != "success":
        raise RuntimeError(
            f"Upstox News API error: {payload}"
        )

    data = payload.get("data", {})

    articles = []

    for instrument_key in instrument_keys:
        instrument_articles = data.get(
            instrument_key,
            [],
        )

        if isinstance(instrument_articles, list):
            for article in instrument_articles:
                article = article.copy()
                article["instrument_key"] = instrument_key
                articles.append(article)

    return articles


def normalize_news(
    articles: list[dict],
) -> pd.DataFrame:

    columns = [
        "instrument_key",
        "headline",
        "summary",
        "published_time",
        "article_url",
        "source",
        "ingested_at",
    ]

    if not articles:
        return pd.DataFrame(columns=columns)

    df = pd.DataFrame(articles)

    # Map API fields to a consistent internal schema.
    df = df.rename(
        columns={
            "heading": "headline",
            "article_link": "article_url",
        }
    )

    required_fields = [
        "instrument_key",
        "headline",
        "summary",
        "published_time",
        "article_url",
    ]

    for column in required_fields:
        if column not in df.columns:
            df[column] = pd.NA

    # API publication timestamps are Unix milliseconds.
    df["published_time"] = pd.to_datetime(
        pd.to_numeric(
            df["published_time"],
            errors="coerce",
        ),
        unit="ms",
        utc=True,
        errors="coerce",
    )

    # Record when this ingestion process received the data.
    # This is not necessarily the provider's original
    # publication or availability timestamp.
    ingested_at = pd.Timestamp.now(tz="UTC")

    df["ingested_at"] = ingested_at

    if "source" not in df.columns:
        df["source"] = "Upstox"

    df["source"] = df["source"].fillna("Upstox")

    df = df[columns]

    # Drop articles without a usable headline or URL.
    df = df.dropna(
        subset=["headline", "article_url"]
    )

    # Remove duplicates within this batch.
    df = df.drop_duplicates(
        subset=["article_url"],
        keep="first",
    )

    return df.reset_index(drop=True)


def save_news(df: pd.DataFrame) -> None:

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if df.empty:
        print("No new articles to save.")
        return

    if OUTPUT_PATH.exists():
        existing = pd.read_csv(
            OUTPUT_PATH,
            parse_dates=["published_time", "ingested_at"],
        )

        combined = pd.concat(
            [existing, df],
            ignore_index=True,
        )

        combined = combined.drop_duplicates(
            subset=["article_url"],
            keep="first",
        )
    else:
        combined = df

    combined.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print("Articles in this batch:", len(df))
    print("Unique articles stored:", len(combined))
    print("Saved to:", OUTPUT_PATH)


def main() -> None:

    print("Fetching Upstox financial news...")

    articles = fetch_news(
        instrument_keys=INSTRUMENT_KEYS,
        page_number=1,
        page_size=20,
    )

    print("Raw articles fetched:", len(articles))

    news_df = normalize_news(articles)

    print("Normalized articles:", len(news_df))

    if not news_df.empty:
        print()
        print(
            news_df[
                [
                    "headline",
                    "published_time",
                    "instrument_key",
                ]
            ].head()
        )

    save_news(news_df)


if __name__ == "__main__":
    main()
