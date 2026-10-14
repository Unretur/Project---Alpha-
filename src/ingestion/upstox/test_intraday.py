import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.ingestion.upstox.intraday import _candles_to_frame, refresh_intraday


class FakeUpstoxClient:
    def __init__(self, candles):
        self.candles = candles
        self.endpoint = None

    def get_v3(self, endpoint):
        self.endpoint = endpoint
        return {"data": {"candles": self.candles}}


class IntradayIngestionTests(unittest.TestCase):
    def test_candle_parser_accepts_optional_open_interest(self):
        frame = _candles_to_frame([
            ["2026-10-14T04:00:00+00:00", 100, 102, 99, 101, 500],
        ])
        self.assertEqual(len(frame), 1)
        self.assertTrue(pd.isna(frame.loc[0, "open_interest"]))
        self.assertEqual(frame.loc[0, "close"], 101)

    def test_refresh_merges_and_deduplicates_existing_history(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nifty50_5m.csv"
            pd.DataFrame([{
                "timestamp": "2026-10-13T09:55:00+00:00",
                "open": 100, "high": 102, "low": 99, "close": 101,
                "volume": 10, "open_interest": None,
            }]).to_csv(path, index=False)

            client = FakeUpstoxClient([
                ["2026-10-14T04:00:00+00:00", 101, 103, 100, 102, 20, None],
                ["2026-10-14T04:05:00+00:00", 102, 104, 101, 103, 25, None],
            ])
            result = refresh_intraday(client, path)

            self.assertIn("/historical-candle/intraday/", client.endpoint)
            self.assertEqual(len(result), 3)
            self.assertEqual(result["timestamp"].duplicated().sum(), 0)
            self.assertTrue(result["timestamp"].is_monotonic_increasing)

    def test_empty_response_does_not_overwrite_existing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nifty50_5m.csv"
            original = "existing-data\n"
            path.write_text(original, encoding="utf-8")
            with self.assertRaises(RuntimeError):
                refresh_intraday(FakeUpstoxClient([]), path)
            self.assertEqual(path.read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main()
