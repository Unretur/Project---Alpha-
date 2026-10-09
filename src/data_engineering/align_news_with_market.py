
from pathlib import Path

import pandas as pd

from src.data_engineering.validation import validate_no_lookahead

MARKET_PATH = Path("data/processed/nifty_macro_aligned.csv")
NEWS_PATH = Path("data/processed/news/news_features.csv")
OUTPUT_PATH = Path("data/processed/nifty_with_news.csv")

def main():
    market = pd.read_csv(MARKET_PATH)
    news = pd.read_csv(NEWS_PATH)

    market["timestamp"] = pd.to_datetime(
        market["timestamp"], utc=True, errors="coerce"
    )
    news["available_time"] = pd.to_datetime(
        news["available_time"], utc=True, errors="coerce"
    )

    market = market.dropna(subset=["timestamp"]).sort_values("timestamp")
    news = news.dropna(subset=["available_time"]).sort_values("available_time")

    if market.empty:
        raise ValueError("Market dataset is empty.")
    if news.empty:
        raise ValueError("News feature dataset is empty.")

    aligned = pd.merge_asof(
        market,
        news,
        left_on="timestamp",
        right_on="available_time",
        direction="backward",
        allow_exact_matches=True,
    )

    matched = aligned["available_time"].notna()

    if matched.any():
        validate_no_lookahead(
            aligned.loc[matched],
            available_column="available_time",
            decision_column="timestamp",
        )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    aligned.to_csv(OUTPUT_PATH, index=False)

    print("News-market alignment completed.")
    print("Market rows:", len(market))
    print("News feature rows:", len(news))
    print("Candles with matched news features:", int(matched.sum()))
    print("Candles without prior news features:", int((~matched).sum()))
    print("Output shape:", aligned.shape)
    print("Saved:", OUTPUT_PATH)

if __name__ == "__main__":
    main()
