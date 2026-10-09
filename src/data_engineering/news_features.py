from pathlib import Path

import pandas as pd


INPUT_PATH = Path("data/processed/news/finbert_sentiment.csv")
OUTPUT_PATH = Path("data/processed/news/news_features.csv")


def build_news_features(news: pd.DataFrame) -> pd.DataFrame:
    """Normalize article-level FinBERT scores while preserving availability time."""
    required = {
        "published_time",
        "ingested_at",
        "positive",
        "neutral",
        "negative",
        "article_url",
    }
    missing = required.difference(news.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    result = news.copy()
    result["published_time"] = pd.to_datetime(
        result["published_time"], utc=True, errors="coerce"
    )
    result["ingested_at"] = pd.to_datetime(
        result["ingested_at"], utc=True, errors="coerce"
    )
    for column in ("positive", "neutral", "negative"):
        result[column] = pd.to_numeric(result[column], errors="coerce")

    result = result.dropna(
        subset=[
            "published_time", "ingested_at", "positive", "neutral", "negative",
            "article_url",
        ]
    ).copy()
    result = result.loc[result["article_url"].astype(str).str.strip().ne("")].copy()

    columns = [
        "article_url",
        "published_time",
        "ingested_at",
        "available_time",
        "news_positive",
        "news_neutral",
        "news_negative",
        "news_sentiment_net",
    ]
    # Keep an empty but valid schema if an ingestion run has no usable articles.
    if result.empty:
        return pd.DataFrame(columns=columns)

    # Retrieval time is a conservative availability proxy, not original
    # provider-availability proof. Never use an article before retrieval.
    result["available_time"] = result[
        ["published_time", "ingested_at"]
    ].max(axis=1)

    result = result.drop_duplicates(subset=["article_url"], keep="first").copy()
    result["news_positive"] = result["positive"]
    result["news_neutral"] = result["neutral"]
    result["news_negative"] = result["negative"]
    result["news_sentiment_net"] = result["positive"] - result["negative"]

    # Retain useful metadata when the source dataset provides it.
    for optional_column in ("headline", "source", "instrument_key"):
        if optional_column in result.columns:
            columns.insert(0, optional_column)

    return (
        result[columns]
        .sort_values(["available_time", "article_url"])
        .reset_index(drop=True)
    )


def main() -> None:
    if not INPUT_PATH.is_file():
        raise FileNotFoundError(f"FinBERT sentiment dataset not found: {INPUT_PATH}")

    news = pd.read_csv(INPUT_PATH)
    features = build_news_features(news)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    features.to_csv(OUTPUT_PATH, index=False)

    print("News feature generation completed.")
    print("Input rows:", len(news))
    print("Usable unique articles:", len(features))
    print("Columns:", features.columns.tolist())
    print("\nSaved:", OUTPUT_PATH)


if __name__ == "__main__":
    main()
