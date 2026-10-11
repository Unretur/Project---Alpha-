import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from src.models.predict_latest import predict_latest
from src.models.train_model import train_and_evaluate


def sample_dataset(rows: int = 360) -> pd.DataFrame:
    timestamps = pd.date_range(
        "2026-01-05 09:15:00", periods=rows, freq="5min", tz="UTC"
    )
    close = 22000 + np.cumsum(np.sin(np.arange(rows) / 7) + 0.2)
    frame = pd.DataFrame(
        {
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
        }
    )
    for horizon in (5, 15, 30):
        steps = horizon // 5
        target = np.full(rows, np.nan)
        target[:-steps] = close[steps:] / close[:-steps] - 1.0
        frame[f"target_return_{horizon}m"] = target
    return frame


class TrainPredictPipelineTests(unittest.TestCase):
    def test_trains_all_horizons_and_saves_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact_dir = root / "artifacts"
            metrics_path = root / "metrics.json"
            report = train_and_evaluate(
                sample_dataset(), artifact_dir=artifact_dir, metrics_path=metrics_path
            )

            self.assertEqual(set(report["horizons"]), {"5m", "15m", "30m"})
            self.assertTrue(metrics_path.is_file())
            for horizon in (5, 15, 30):
                self.assertTrue((artifact_dir / f"nifty_return_{horizon}m.joblib").is_file())
                result = report["horizons"][f"{horizon}m"]
                self.assertIn(result["selected_model"], {"ridge", "hist_gradient_boosting"})
                self.assertIn("mae", result["test_metrics"])
                self.assertIn("mae", result["test_zero_return_baseline"])
                self.assertIsInstance(result["deployment_eligible"], bool)

    def test_prediction_outputs_all_horizons_in_research_mode(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact_dir = root / "artifacts"
            train_and_evaluate(
                sample_dataset(),
                artifact_dir=artifact_dir,
                metrics_path=root / "metrics.json",
            )
            predictions = predict_latest(
                sample_dataset(), artifact_dir=artifact_dir, allow_research_model=True
            )
            self.assertEqual([item["horizon_minutes"] for item in predictions], [5, 15, 30])
            self.assertTrue(
                all(np.isfinite(item["predicted_forward_return"]) for item in predictions)
            )

    def test_prediction_refuses_missing_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(FileNotFoundError):
                predict_latest(sample_dataset(), artifact_dir=Path(temporary))


if __name__ == "__main__":
    unittest.main()
