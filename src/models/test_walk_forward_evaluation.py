import unittest

import pandas as pd

from src.models.test_baseline import sample_dataset
from src.models.walk_forward_evaluation import _metrics, evaluate_walk_forward


class WalkForwardEvaluationTests(unittest.TestCase):
    def test_evaluates_each_horizon_across_sequential_folds(self):
        report = evaluate_walk_forward(
            sample_dataset(rows=360), n_splits=3, min_train_fraction=0.5
        )
        self.assertEqual(report["method"], "expanding_window_walk_forward")
        self.assertFalse(report["selection_used_test_folds"])
        self.assertEqual(set(report["horizons"]), {"5m", "15m", "30m"})

        for horizon, result in report["horizons"].items():
            horizon_minutes = int(horizon.removesuffix("m"))
            self.assertEqual(len(result["folds"]), 3)
            self.assertGreater(result["aggregate_model_metrics"]["rows"], 0)
            self.assertGreater(result["aggregate_zero_return_baseline"]["mae"], 0)
            for fold in result["folds"]:
                self.assertGreater(fold["train_rows"], 0)
                self.assertGreater(fold["test_rows"], 0)
                self.assertLess(
                    pd.Timestamp(fold["train_end"])
                    + pd.Timedelta(minutes=horizon_minutes),
                    pd.Timestamp(fold["test_start"]),
                )

    def test_zero_return_baseline_has_no_directional_coverage(self):
        import numpy as np

        actual = np.array([0.1, -0.1, 0.0])
        zero_predictions = np.zeros_like(actual)
        metrics = _metrics(actual, zero_predictions)

        self.assertAlmostEqual(metrics["sign_accuracy"], 1 / 3)
        self.assertEqual(metrics["directional_coverage"], 0.0)
        self.assertIsNone(metrics["directional_accuracy_when_nonzero"])

    def test_directional_accuracy_is_scored_only_for_nonzero_predictions(self):
        import numpy as np

        actual = np.array([0.1, -0.1, 0.0])
        predictions = np.array([0.2, -0.1, 0.0])
        metrics = _metrics(actual, predictions)

        self.assertAlmostEqual(metrics["directional_coverage"], 2 / 3)
        self.assertEqual(metrics["directional_accuracy_when_nonzero"], 1.0)

    def test_rejects_invalid_split_count(self):
        with self.assertRaises(ValueError):
            evaluate_walk_forward(sample_dataset(), n_splits=1)

    def test_rejects_too_few_rows_for_folds(self):
        with self.assertRaises(ValueError):
            evaluate_walk_forward(
                sample_dataset(rows=12), n_splits=4, min_train_fraction=0.8
            )


if __name__ == "__main__":
    unittest.main()
