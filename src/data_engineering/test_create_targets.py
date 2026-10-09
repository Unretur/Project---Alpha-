import unittest

import pandas as pd

from src.data_engineering.create_targets import add_forward_return_targets


class ForwardReturnTargetTests(unittest.TestCase):
    def test_exact_horizons_create_expected_returns(self):
        timestamps = pd.date_range(
            "2026-01-05 09:15:00", periods=7, freq="5min", tz="UTC"
        )
        frame = pd.DataFrame(
            {"timestamp": timestamps, "close": [100, 101, 102, 103, 104, 105, 106]}
        )

        result = add_forward_return_targets(frame)

        self.assertAlmostEqual(result.loc[0, "target_return_5m"], 0.01)
        self.assertAlmostEqual(result.loc[0, "target_return_15m"], 0.03)
        self.assertAlmostEqual(result.loc[0, "target_return_30m"], 0.06)
        self.assertEqual(result.loc[0, "target_direction_5m"], "up")
        self.assertTrue(pd.isna(result.loc[6, "target_return_5m"]))

    def test_missing_future_timestamp_is_not_filled_from_later_row(self):
        timestamps = pd.to_datetime(
            [
                "2026-01-05T09:15:00Z",
                "2026-01-05T09:20:00Z",
                "2026-01-05T09:30:00Z",
            ],
            utc=True,
        )
        frame = pd.DataFrame({"timestamp": timestamps, "close": [100, 101, 110]})

        result = add_forward_return_targets(frame)

        # There is no 09:25 candle, so the 5-minute target at 09:20 is unknown.
        self.assertTrue(pd.isna(result.loc[1, "target_return_5m"]))
        # There is no exact 09:20 candle after the first row? It exists, so 09:15 -> 09:20 is valid.
        self.assertAlmostEqual(result.loc[0, "target_return_5m"], 0.01)
        # 09:15 + 15m = 09:30 exists exactly.
        self.assertAlmostEqual(result.loc[0, "target_return_15m"], 0.10)

    def test_duplicate_timestamps_are_rejected(self):
        frame = pd.DataFrame(
            {
                "timestamp": [
                    "2026-01-05T09:15:00Z",
                    "2026-01-05T09:15:00Z",
                ],
                "close": [100, 101],
            }
        )
        with self.assertRaises(ValueError):
            add_forward_return_targets(frame)


if __name__ == "__main__":
    unittest.main()
