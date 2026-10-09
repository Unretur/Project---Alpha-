import unittest

import numpy as np
import pandas as pd

from src.models.baseline import build_feature_frame, chronological_split, run_baselines


def sample_dataset(rows: int = 240) -> pd.DataFrame:
    timestamps = pd.date_range(
        "2026-01-05 09:15:00", periods=rows, freq="5min", tz="UTC"
    )
    close = 22000 + np.cumsum(np.sin(np.arange(rows) / 7) + 0.2)
    frame = pd.DataFrame({
        "timestamp": timestamps,
        "open": close - 1.0,
        "high": close + 3.0,
        "low": close - 3.0,
        "close": close,
        "volume": 1000 + np.arange(rows),
        "open_interest": 50000 + np.arange(rows) * 2,
        "vix": 15 + np.arange(rows) * 0.001,
        "us10y": 4.0 + np.arange(rows) * 0.0001,
        "fed_funds": 3.8,
        "usd_inr_fred": 85 + np.arange(rows) * 0.0005,
    })
    for horizon in (5, 15, 30):
        steps = horizon // 5
        target = np.full(rows, np.nan)
        target[:-steps] = close[steps:] / close[:-steps] - 1.0
        frame[f"target_return_{horizon}m"] = target
        frame[f"target_direction_{horizon}m"] = np.where(
            np.isnan(target), pd.NA, np.where(target > 0, "up", np.where(target < 0, "down", "flat"))
        )
    return frame


class BaselineModelTests(unittest.TestCase):
    def test_features_exclude_targets_metadata_and_are_lagged(self):
        feature_frame, features = build_feature_frame(sample_dataset())
        self.assertTrue(features)
        self.assertFalse(any(name.startswith("target_") for name in features))
        self.assertFalse(any(name.endswith("_available_time") for name in features))
        self.assertTrue(np.isnan(feature_frame.loc[1, "close_return_lag_1"]))
        self.assertAlmostEqual(
            feature_frame.loc[2, "close_return_lag_1"],
            feature_frame.loc[1, "close"] / feature_frame.loc[0, "close"] - 1.0,
        )

    def test_chronological_splits_are_ordered_and_purged(self):
        data, _ = build_feature_frame(sample_dataset())
        splits = chronological_split(data)
        self.assertLess(splits["train"]["timestamp"].max(), splits["validation"]["timestamp"].min())
        self.assertLess(splits["validation"]["timestamp"].max(), splits["test"]["timestamp"].min())
        self.assertLess(
            splits["train"]["timestamp"].max() + pd.Timedelta(minutes=30),
            splits["validation"]["timestamp"].min(),
        )
        self.assertLess(
            splits["validation"]["timestamp"].max() + pd.Timedelta(minutes=30),
            splits["test"]["timestamp"].min(),
        )

    def test_baselines_produce_test_metrics_for_each_horizon(self):
        result = run_baselines(sample_dataset())
        self.assertEqual(set(result["horizons"]), {"5m", "15m", "30m"})
        for metrics in result["horizons"].values():
            self.assertGreater(metrics["test_rows"], 0)
            self.assertGreaterEqual(metrics["test"]["mae"], 0)
            self.assertGreaterEqual(metrics["test"]["rmse"], 0)
            self.assertIn("zero_return_baseline_test", metrics)


if __name__ == "__main__":
    unittest.main()
