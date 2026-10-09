from pathlib import Path

import numpy as np
import pandas as pd

from src.data_engineering.validation import validate_no_lookahead


MARKET_PATH = Path("data/processed/nifty_macro_aligned.csv")
NEWS_PATH = Path("data/processed/news/news_features.csv")
OUTPUT_PATH = Path("data/processed/nifty_with_news.csv")

WINDOWS = {
    "5m": pd.Timedelta(minutes=5),
    "15m": pd.Timedelta(minutes=15),
    "30m": pd.Timedelta(minutes=30),
}

NEWS_COLUMNS = {
    "available_time",
    "news_positive",
    "news_neutral",
    "news_negative",
    "news_sentiment_net",
    "article_url",
}


def add_rolling_news_features(
    market: pd.DataFrame,
    news: pd.DataFrame,
) -> pd.DataFrame:
    """Add causal rolling news features using articles available by each candle."""
    if "timestamp" not in market.columns:
        raise ValueError("Market dataset must contain a 'timestamp' column.")
    missing = NEWS_COLUMNS.difference(news.columns)
    if missing:
        raise ValueError(f"News features missing columns: {sorted(missing)}")

    result = market.copy()
    result["timestamp"] = pd.to_datetime(
        result["timestamp"], utc=True, errors="coerce"
    )
    news = news.copy()
    news["available_time"] = pd.to_datetime(
        news["available_time"], utc=True, errors="coerce"
    )

    result = (
        result.dropna(subset=["timestamp"])
        .sort_values("timestamp")
        .reset_index(drop=True)
    )
    news = news.dropna(subset=["available_time"]).copy()

    for column in ("news_positive", "news_neutral", "news_negative", "news_sentiment_net"):
        news[column] = pd.to_numeric(news[column], errors="coerce")

    news = (
        news.dropna(subset=[
            "news_positive", "news_neutral", "news_negative", "news_sentiment_net"
        ])
        .drop_duplicates(subset=["article_url"], keep="first")
        .sort_values("available_time")
        .reset_index(drop=True)
    )

    # Initialize consistently typed outputs, including when no news is available.
    for window_name in WINDOWS:
        result[f"news_count_{window_name}"] = 0
        for metric in ("positive_mean", "neutral_mean", "negative_mean", "sentiment_net_mean"):
            result[f"news_{metric}_{window_name}"] = np.nan

    result["latest_news_available_time"] = pd.Series(
        pd.NaT, index=result.index, dtype="datetime64[ns, UTC]"
    )
    if news.empty or result.empty:
        return result

    # Explicitly normalize to nanoseconds. Pandas may otherwise use
    # microsecond-resolution integer values, which would mismatch Timedelta.value.
    news_times = (
        news["available_time"]
        .dt.tz_convert("UTC")
        .dt.tz_localize(None)
        .to_numpy(dtype="datetime64[ns]")
        .astype("int64")
    )
    decision_times = (
        result["timestamp"]
        .dt.tz_convert("UTC")
        .dt.tz_localize(None)
        .to_numpy(dtype="datetime64[ns]")
        .astype("int64")
    )
    metric_columns = {
        "positive_mean": "news_positive",
        "neutral_mean": "news_neutral",
        "negative_mean": "news_negative",
        "sentiment_net_mean": "news_sentiment_net",
    }

    # Prefix sums provide efficient O((market + news) log(news)) window aggregation.
    prefix_sums = {
        metric: np.concatenate(
            ([0.0], np.cumsum(news[column].to_numpy(dtype=float)))
        )
        for metric, column in metric_columns.items()
    }

    for row_index, decision_ns in enumerate(decision_times):
        right = int(np.searchsorted(news_times, decision_ns, side="right"))
        if right == 0:
            continue

        result.at[row_index, "latest_news_available_time"] = news.loc[
            right - 1, "available_time"
        ]

        for window_name, window_delta in WINDOWS.items():
            lower_ns = decision_ns - int(window_delta.value)
            left = int(np.searchsorted(news_times, lower_ns, side="left"))
            count = right - left
            result.at[row_index, f"news_count_{window_name}"] = count
            if count == 0:
                continue
            for metric, prefix in prefix_sums.items():
                value = (prefix[right] - prefix[left]) / count
                result.at[row_index, f"news_{metric}_{window_name}"] = value

    matched = result["latest_news_available_time"].notna()
    if matched.any():
        validate_no_lookahead(
            result.loc[matched].rename(
                columns={
                    "latest_news_available_time": "available_time",
                    "timestamp": "decision_timestamp",
                }
            ),
            available_column="available_time",
            decision_column="decision_timestamp",
        )

    return result


def main() -> None:
    if not MARKET_PATH.is_file():
        raise FileNotFoundError(f"Market dataset not found: {MARKET_PATH}")
    if not NEWS_PATH.is_file():
        raise FileNotFoundError(f"News features not found: {NEWS_PATH}")

    market = pd.read_csv(MARKET_PATH)
    news = pd.read_csv(NEWS_PATH)

    aligned = add_rolling_news_features(market, news)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    aligned.to_csv(OUTPUT_PATH, index=False)

    matched = aligned["latest_news_available_time"].notna()
    print("News-market alignment completed.")
    print("Market rows:", len(aligned))
    print("Article-level news rows:", len(news))
    print("Candles with prior news:", int(matched.sum()))
    print("Candles without prior news:", int((~matched).sum()))
    print("Output shape:", aligned.shape)
    print("Saved:", OUTPUT_PATH)


if __name__ == "__main__":
    main()
