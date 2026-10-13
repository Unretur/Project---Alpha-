"""Unit tests for the research backtesting engine."""
import unittest
import pandas as pd
from src.models.backtest import run_backtest


class BacktestTests(unittest.TestCase):
    def setUp(self):
        self.frame = pd.DataFrame({
            "timestamp": pd.date_range("2026-01-01", periods=4, freq="h", tz="UTC"),
            "predicted_return": [0.02, -0.03, 0.001, 0.04],
            "actual_forward_return": [0.01, 0.02, -0.01, 0.03],
        })

    def test_signals_costs_and_net_returns(self):
        trades, metrics = run_backtest(
            self.frame, threshold=0.005, round_trip_cost_bps=10, periods_per_year=4
        )
        self.assertEqual(trades["signal"].tolist(), [1, -1, 0, 1])
        self.assertAlmostEqual(trades.loc[0, "net_return"], 0.009)
        self.assertAlmostEqual(trades.loc[1, "net_return"], -0.021)
        self.assertEqual(metrics["trades_taken"], 3)
        self.assertEqual(metrics["long_trades"], 2)
        self.assertEqual(metrics["short_trades"], 1)

    def test_rejects_missing_columns(self):
        with self.assertRaisesRegex(ValueError, "Missing required columns"):
            run_backtest(pd.DataFrame({"timestamp": ["2026-01-01"]}))

    def test_rejects_duplicate_timestamps(self):
        duplicate = pd.concat([self.frame, self.frame.iloc[[0]]], ignore_index=True)
        with self.assertRaisesRegex(ValueError, "unique"):
            run_backtest(duplicate)

    def test_rejects_non_finite_returns(self):
        invalid = self.frame.copy()
        invalid.loc[0, "predicted_return"] = float("inf")
        with self.assertRaisesRegex(ValueError, "finite"):
            run_backtest(invalid)

    def test_flat_signal_has_no_cost(self):
        flat = self.frame.copy()
        flat["predicted_return"] = 0.0
        trades, metrics = run_backtest(flat, round_trip_cost_bps=20)
        self.assertTrue((trades["net_return"] == 0).all())
        self.assertEqual(metrics["trades_taken"], 0)
        self.assertIsNone(metrics["win_rate_net"])


    def test_horizon_prevents_overlapping_trades(self):
        data = pd.DataFrame({
            "timestamp": pd.date_range("2026-01-01", periods=5, freq="5min", tz="UTC"),
            "predicted_return": [0.01, 0.02, -0.02, 0.01, 0.01],
            "actual_forward_return": [0.01, 0.02, -0.02, 0.01, 0.01],
            "horizon_minutes": [15, 15, 15, 15, 15],
        })
        trades, metrics = run_backtest(data, round_trip_cost_bps=0)
        self.assertEqual(trades["signal"].tolist(), [1, 0, 0, 1, 0])
        self.assertEqual(metrics["trades_taken"], 2)
        self.assertEqual(metrics["signals_skipped_while_position_open"], 3)



if __name__ == "__main__":
    unittest.main()
