import unittest

import pandas as pd

from src.data_engineering.align_news_with_market import add_rolling_news_features
from src.data_engineering.news_features import build_news_features


class NewsFeatureTests(unittest.TestCase):
    def test_news_availability_is_not_before_ingestion(self):
        source = pd.DataFrame(
            {
                "published_time": ["2026-10-09T09:00:00Z"],
                "ingested_at": ["2026-10-09T09:02:00Z"],
                "positive": [0.7],
                "neutral": [0.2],
                "negative": [0.1],
                "article_url": ["https://example.test/article/1"],
            }
        )

        features = build_news_features(source)

        self.assertEqual(len(features), 1)
        self.assertEqual(
            features.loc[0, "available_time"],
            pd.Timestamp("2026-10-09T09:02:00Z"),
        )
        self.assertAlmostEqual(features.loc[0, "news_sentiment_net"], 0.6)

    def test_rolling_features_exclude_future_news_and_obey_windows(self):
        market = pd.DataFrame(
            {
                "timestamp": [
                    "2026-10-09T10:00:00Z",
                    "2026-10-09T10:05:00Z",
                    "2026-10-09T10:16:00Z",
                ],
                "close": [100.0, 101.0, 102.0],
            }
        )
        news = pd.DataFrame(
            {
                "available_time": [
                    "2026-10-09T09:54:00Z",
                    "2026-10-09T10:03:00Z",
                    "2026-10-09T10:10:00Z",
                ],
                "news_positive": [0.7, 0.2, 0.6],
                "news_neutral": [0.2, 0.3, 0.3],
                "news_negative": [0.1, 0.5, 0.1],
                "news_sentiment_net": [0.6, -0.3, 0.5],
                "article_url": ["a", "b", "c"],
            }
        )

        aligned = add_rolling_news_features(market, news)

        self.assertEqual(aligned.loc[0, "news_count_5m"], 0)
        self.assertEqual(aligned.loc[0, "news_count_15m"], 1)
        self.assertEqual(aligned.loc[1, "news_count_5m"], 1)
        self.assertEqual(aligned.loc[1, "news_count_15m"], 2)
        self.assertEqual(aligned.loc[2, "news_count_5m"], 0)
        self.assertEqual(aligned.loc[2, "news_count_15m"], 2)

        available = aligned["latest_news_available_time"].dropna()
        decision = aligned.loc[available.index, "timestamp"]
        self.assertTrue((available <= decision).all())

    def test_empty_news_keeps_market_rows_and_zero_counts(self):
        market = pd.DataFrame(
            {"timestamp": ["2026-10-09T10:00:00Z", "2026-10-09T10:05:00Z"]}
        )
        empty_news = pd.DataFrame(
            columns=[
                "available_time",
                "news_positive",
                "news_neutral",
                "news_negative",
                "news_sentiment_net",
                "article_url",
            ]
        )

        aligned = add_rolling_news_features(market, empty_news)

        self.assertEqual(len(aligned), len(market))
        self.assertEqual(aligned["news_count_5m"].tolist(), [0, 0])
        self.assertTrue(aligned["latest_news_available_time"].isna().all())


if __name__ == "__main__":
    unittest.main()
