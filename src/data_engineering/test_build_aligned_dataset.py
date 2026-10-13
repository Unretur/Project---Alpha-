import unittest

import pandas as pd

from src.data_engineering.build_aligned_dataset import resolve_usd_inr_columns


class ResolveUsdInrColumnsTests(unittest.TestCase):
    def test_fred_only_renames_value_and_availability(self):
        frame = pd.DataFrame(
            {
                "timestamp": ["2026-01-01T03:45:00Z"],
                "usd_inr": [89.84],
                "usd_inr_available_time": ["2026-01-01T00:00:00Z"],
            }
        )

        result = resolve_usd_inr_columns(frame)

        self.assertIn("usd_inr_fred", result.columns)
        self.assertIn("usd_inr_fred_available_time", result.columns)
        self.assertNotIn("usd_inr_available_time", result.columns)
        self.assertEqual(result.loc[0, "usd_inr_fred"], 89.84)
        self.assertEqual(
            result.loc[0, "usd_inr_fred_available_time"],
            "2026-01-01T00:00:00Z",
        )

    def test_fred_and_rbi_keep_separate_values_and_timestamps(self):
        frame = pd.DataFrame(
            {
                "timestamp": ["2026-01-01T03:45:00Z"],
                "usd_inr_x": [89.84],
                "usd_inr_y": [89.90],
                "usd_inr_available_time": ["2026-01-01T00:00:00Z"],
                "rbi_fx_available_time": ["2025-12-31T00:00:00Z"],
            }
        )

        result = resolve_usd_inr_columns(frame)

        self.assertEqual(result.loc[0, "usd_inr_fred"], 89.84)
        self.assertEqual(result.loc[0, "usd_inr_rbi"], 89.90)
        self.assertEqual(
            result.loc[0, "usd_inr_fred_available_time"],
            "2026-01-01T00:00:00Z",
        )
        self.assertEqual(
            result.loc[0, "usd_inr_rbi_available_time"],
            "2025-12-31T00:00:00Z",
        )
        self.assertNotIn("usd_inr_available_time", result.columns)
        self.assertNotIn("rbi_fx_available_time", result.columns)


if __name__ == "__main__":
    unittest.main()
