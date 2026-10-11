import unittest

import numpy as np

from src.models.evaluation_diagnostics import evaluate_predictions


class EvaluationDiagnosticsTests(unittest.TestCase):
    def test_reports_error_and_directional_coverage(self):
        actual = np.array([0.1, -0.2, 0.3, -0.4])
        predicted = np.array([0.2, -0.1, 0.0, -0.5])

        result = evaluate_predictions(actual, predicted)

        self.assertEqual(result["rows"], 4)
        self.assertAlmostEqual(result["directional_coverage"], 0.75)
        self.assertAlmostEqual(result["directional_accuracy_when_nonzero"], 1.0)
        self.assertGreaterEqual(result["mae"], 0.0)
        self.assertGreaterEqual(result["rmse"], 0.0)

    def test_all_zero_predictions_have_no_conditional_directional_accuracy(self):
        actual = np.array([0.1, -0.2, 0.3])
        predicted = np.zeros(3)

        result = evaluate_predictions(actual, predicted)

        self.assertEqual(result["directional_coverage"], 0.0)
        self.assertIsNone(result["directional_accuracy_when_nonzero"])

    def test_rejects_empty_or_mismatched_arrays(self):
        with self.assertRaises(ValueError):
            evaluate_predictions(np.array([]), np.array([]))
        with self.assertRaises(ValueError):
            evaluate_predictions(np.array([1.0]), np.array([1.0, 2.0]))


if __name__ == "__main__":
    unittest.main()
