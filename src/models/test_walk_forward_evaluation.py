import unittest

import numpy as np
import pandas as pd

from src.models.test_baseline import sample_dataset
from src.models.walk_forward_evaluation import evaluate_walk_forward


class WalkForwardEvaluationTests(unittest.TestCase):
    def test_evaluates_each_horizon_across_sequential_folds(self):
        report = evaluate_walk_forward(
            sample_dataset(rows=360), n_splits=3, min_train_fraction=0.5
        )
        self.assertEqual(report["method"], "expanding_window_walk_forward")
        self.assertFalse(report["selection_used_test_folds"])
        self.assertEqual(set(report["horizons"]), {"5m", "15m", "30m"})

        for result in report["horizons"].values():
            self.assertEqual(len(result["folds"]), 3)
            self.assertGreater(result["aggregate_model_metrics"]["rows"], 0)
            self.assertGreater(result["aggregate_zero_return_baseline"]["mae"], 0)
            for fold in result["folds"]:
                self.assertGreater(fold["train_rows"], 0)
                self.assertGreater(fold["test_rows"], 0)
                self.assertLess(
                    pd.Timestamp(fold["train_end"])
                    + pd.Timedelta(minutes=30),
                    pd.Timestamp(fold["test_start"]),
                )

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
