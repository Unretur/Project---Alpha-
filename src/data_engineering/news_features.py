
from pathlib import Path

import pandas as pd


INPUT_PATH = Path(
    "data/processed/news/finbert_sentiment.csv"
)

OUTPUT_PATH = Path(
    "data/processed/news/news_features.csv"
)


def build_news_features(
    news: pd.DataFrame,
) -> pd.DataFrame:
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
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    result = news.copy()

    result["published_time"] = pd.to_datetime(
        result["published_time"],
        utc=True,
        errors="coerce",
    )

    result["ingested_at"] = pd.to_datetime(
        result["ingested_at"],
        utc=True,
        errors="coerce",
    )

    for column in ["positive", "neutral", "negative"]:
        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        )

    result = result.dropna(
        subset=[
            "published_time",
            "ingested_at",
            "positive",
            "neutral",
            "negative",
        ]
    )

    # A conservative availability proxy: the article must
    # have been published and retrieved by our ingestion run.
    # This is NOT proof of the provider's original availability.
    result["available_time"] = result[
        ["published_time", "ingested_at"]
    ].max(axis=1)

    # Avoid counting duplicate URLs more than once.
    result = result.drop_duplicates(
        subset=["article_url"],
        keep="first",
    )

    result["sentiment_net"] = (
        result["positive"] - result["negative"]
    )

    # Aggregate articles with the same availability timestamp.
    features = (
        result.groupby("available_time", as_index=False)
        .agg(
            news_positive_mean=("positive", "mean"),
            news_negative_mean=("negative", "mean"),
            news_neutral_mean=("neutral", "mean"),
            news_sentiment_net=("sentiment_net", "mean"),
            news_article_count=("article_url", "nunique"),
        )
        .sort_values("available_time")
        .reset_index(drop=True)
    )

    return features


def main() -> None:
    news = pd.read_csv(INPUT_PATH)

    features = build_news_features(news)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    features.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print("News feature generation completed.")
    print("Input articles:", len(news))
    print("Feature rows:", len(features))
    print("Columns:", features.columns.tolist())
    print("\nFeatures:")
    print(features.to_string(index=False))
    print("\nSaved:", OUTPUT_PATH)


if __name__ == "__main__":
    main()
