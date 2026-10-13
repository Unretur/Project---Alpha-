import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.models.test_train_predict_pipeline import sample_dataset
from src.models.train_model import train_and_evaluate
from src.paper_trading.signal_engine import generate_paper_signals, write_signal_outputs


class PaperSignalEngineTests(unittest.TestCase):
    def test_stale_or_ineligible_models_cannot_authorize_execution(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifacts = root / "artifacts"
            dataset = sample_dataset()
            train_and_evaluate(
                dataset, artifact_dir=artifacts, metrics_path=root / "metrics.json"
            )
            now = datetime(2026, 10, 13, tzinfo=timezone.utc)
            signals = generate_paper_signals(
                dataset,
                artifact_dir=artifacts,
                now=now,
                max_data_age_minutes=15,
            )
            self.assertEqual([s["horizon_minutes"] for s in signals], [5, 15, 30])
            self.assertTrue(all(s["execution_allowed"] is False for s in signals))
            self.assertTrue(all(s["paper_action"] == "HOLD" for s in signals))
            self.assertTrue(all("proposed_signal" in s for s in signals))

    def test_signal_ledger_deduplicates_repeated_runs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            row = {
                "signal_id": "NIFTY50-5m-2026-10-13T09:15:00+00:00",
                "instrument": "NIFTY 50",
                "paper_action": "HOLD",
            }
            write_signal_outputs([row], output_path=root / "latest.json", ledger_path=root / "ledger.csv")
            write_signal_outputs([row], output_path=root / "latest.json", ledger_path=root / "ledger.csv")
            ledger = pd.read_csv(root / "ledger.csv")
            self.assertEqual(len(ledger), 1)


if __name__ == "__main__":
    unittest.main()
