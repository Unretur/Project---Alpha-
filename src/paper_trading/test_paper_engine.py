import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

from src.paper_trading.paper_engine import run_paper_trading


class PaperTradingEngineTests(unittest.TestCase):
    def setUp(self):
        self.data = pd.DataFrame({
            "timestamp": ["2026-10-14T09:15:00Z", "2026-10-14T09:20:00Z",
                          "2026-10-14T09:25:00Z", "2026-10-14T09:30:00Z"],
            "close": [100.0, 101.0, 102.0, 103.0],
        })
        self.signal = {
            "signal_id": "NIFTY50-5m-test", "instrument": "NIFTY 50",
            "timestamp": "2026-10-14T09:15:00+00:00", "horizon_minutes": 5,
            "paper_action": "LONG", "execution_allowed": True, "model_name": "test-model",
        }

    def test_ineligible_signal_does_not_open_position(self):
        with tempfile.TemporaryDirectory() as tmp:
            signal = {**self.signal, "execution_allowed": False}
            result = run_paper_trading([signal], self.data, state_dir=Path(tmp))
            self.assertEqual(result["summary"]["open_positions"], 0)
            self.assertEqual(result["summary"]["opened_this_run"], 0)

    def test_position_opens_then_closes_with_costs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = run_paper_trading([self.signal], self.data.iloc[:1], state_dir=root,
                                      now=datetime(2026, 10, 14, 9, 15, tzinfo=timezone.utc))
            self.assertEqual(first["summary"]["open_positions"], 1)
            # Later run: the candle at the 5-minute expiry is available.
            second = run_paper_trading([self.signal], self.data, state_dir=root,
                                       now=datetime(2026, 10, 14, 9, 30, tzinfo=timezone.utc))
            self.assertEqual(second["summary"]["open_positions"], 0)
            self.assertEqual(second["summary"]["closed_trades"], 1)
            self.assertEqual(second["summary"]["closed_this_run"], 1)
            self.assertGreater(second["summary"]["realized_net_pnl"], 0)

    def test_repeated_run_does_not_duplicate_trade(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_paper_trading([self.signal], self.data.iloc[:1], state_dir=root)
            run_paper_trading([self.signal], self.data, state_dir=root)
            again = run_paper_trading([self.signal], self.data, state_dir=root)
            self.assertEqual(again["summary"]["closed_trades"], 1)
            self.assertEqual(again["summary"]["opened_this_run"], 0)


if __name__ == "__main__":
    unittest.main()
