import unittest

from src.models.test_baseline import sample_dataset
from src.models.feature_ablation import evaluate_feature_groups


class FeatureAblationTests(unittest.TestCase):
    def test_evaluates_price_macro_and_combined_groups(self):
        report = evaluate_feature_groups(sample_dataset(rows=360))
        groups = report["feature_groups"]
        self.assertEqual(
            set(groups),
            {"price_action_only", "macro_only", "price_action_plus_macro"},
        )
        for result in groups.values():
            self.assertGreater(result["feature_count"], 0)
            self.assertEqual(
                set(result["evaluation"]["horizons"]), {"5m", "15m", "30m"}
            )
            for horizon_result in result["evaluation"]["horizons"].values():
                self.assertEqual(len(horizon_result["folds"]), 4)
                self.assertGreater(horizon_result["aggregate_model_metrics"]["rows"], 0)


if __name__ == "__main__":
    unittest.main()
