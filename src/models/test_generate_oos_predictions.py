"""Tests for out-of-sample prediction generation."""
import unittest
import numpy as np
import pandas as pd

from src.models.baseline import HORIZONS
from src.models.generate_oos_predictions import generate_oos_predictions


class GenerateOosPredictionsTests(unittest.TestCase):
    def make_dataset(self, n=240):
        rng = np.random.default_rng(7)
        close = 100 + np.cumsum(rng.normal(0, 0.2, n))
        frame = pd.DataFrame({
            "timestamp": pd.date_range("2026-01-01", periods=n, freq="5min", tz="UTC"),
            "open": close * (1 + rng.normal(0, 0.0002, n)),
            "high": close * 1.002,
            "low": close * 0.998,
            "close": close,
            "volume": rng.integers(1, 1000, n),
            "open_interest": rng.integers(100, 200, n),
        })
        for h in HORIZONS:
            frame[f"target_return_{h}m"] = frame["close"].shift(-(h // 5)) / frame["close"] - 1
        return frame

    def test_outputs_have_required_columns_and_sorted_unique_timestamps(self):
        outputs = generate_oos_predictions(self.make_dataset(), n_splits=3)
        self.assertEqual(set(outputs), set(HORIZONS))
        for horizon, frame in outputs.items():
            self.assertTrue({
                "timestamp", "predicted_return", "actual_forward_return",
                "horizon_minutes", "fold", "train_end"
            }.issubset(frame.columns))
            self.assertFalse(frame["timestamp"].duplicated().any())
            self.assertTrue(frame["timestamp"].is_monotonic_increasing)
            self.assertTrue((frame["horizon_minutes"] == horizon).all())
            self.assertTrue(np.isfinite(frame["predicted_return"]).all())

    def test_rejects_invalid_fold_count(self):
        with self.assertRaisesRegex(ValueError, "at least 2"):
            generate_oos_predictions(self.make_dataset(), n_splits=1)


if __name__ == "__main__":
    unittest.main()
