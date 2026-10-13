"""Research backtester for already-generated out-of-sample predictions."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = ("timestamp", "predicted_return", "actual_forward_return")


def run_backtest(
    predictions: pd.DataFrame,
    *,
    threshold: float = 0.0,
    round_trip_cost_bps: float = 10.0,
    periods_per_year: int = 252 * 75,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Evaluate OOS returns; if horizon_minutes is present, prevent overlapping trades.

    This is a research approximation, not a broker execution simulator. Without
    horizon_minutes, callers must provide non-overlapping opportunities.
    """
    missing = set(REQUIRED_COLUMNS).difference(predictions.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    if threshold < 0 or round_trip_cost_bps < 0 or periods_per_year <= 0:
        raise ValueError("threshold/cost must be non-negative and periods_per_year positive.")
    if predictions.empty:
        raise ValueError("At least one prediction row is required.")

    keep = list(REQUIRED_COLUMNS)
    has_horizon = "horizon_minutes" in predictions.columns
    if has_horizon:
        keep.append("horizon_minutes")
    trades = predictions.loc[:, keep].copy()
    trades["timestamp"] = pd.to_datetime(trades["timestamp"], utc=True, errors="raise")
    if trades["timestamp"].isna().any() or trades["timestamp"].duplicated().any():
        raise ValueError("Trade timestamps must be non-null and unique.")
    trades = trades.sort_values("timestamp").reset_index(drop=True)
    for column in ("predicted_return", "actual_forward_return"):
        trades[column] = pd.to_numeric(trades[column], errors="raise")
        if not np.isfinite(trades[column].to_numpy(dtype=float)).all():
            raise ValueError(f"{column} must contain only finite values.")

    pred = trades["predicted_return"].to_numpy(dtype=float)
    actual = trades["actual_forward_return"].to_numpy(dtype=float)
    proposed = np.where(pred > threshold, 1, np.where(pred < -threshold, -1, 0))
    trades["proposed_signal"] = proposed
    if has_horizon:
        horizons = pd.to_numeric(trades["horizon_minutes"], errors="raise").to_numpy(dtype=float)
        if not np.isfinite(horizons).all() or (horizons <= 0).any():
            raise ValueError("horizon_minutes must contain finite positive values.")
        signals = np.zeros(len(trades), dtype=int)
        exits = []
        next_entry = pd.Timestamp.min.tz_localize("UTC")
        for i, timestamp in enumerate(trades["timestamp"]):
            if timestamp >= next_entry and proposed[i] != 0:
                signals[i] = int(proposed[i])
                next_entry = timestamp + pd.Timedelta(minutes=float(horizons[i]))
            exits.append(timestamp + pd.Timedelta(minutes=float(horizons[i])))
        trades["exit_timestamp"] = exits
        trades["signal"] = signals
    else:
        trades["signal"] = proposed

    trades["gross_return"] = trades["signal"] * actual
    trades["cost_return"] = np.where(
        trades["signal"] != 0, round_trip_cost_bps / 10000.0, 0.0
    )
    trades["net_return"] = trades["gross_return"] - trades["cost_return"]
    trades["equity"] = (1.0 + trades["net_return"]).cumprod()
    trades["running_peak"] = trades["equity"].cummax()
    trades["drawdown"] = trades["equity"] / trades["running_peak"] - 1.0

    active = trades.loc[trades["signal"] != 0, "net_return"]
    net = trades["net_return"].to_numpy(dtype=float)
    std = float(np.std(net, ddof=1)) if len(net) > 1 else 0.0
    sharpe = float(np.mean(net) / std * np.sqrt(periods_per_year)) if std > 0 else None
    metrics: dict[str, Any] = {
        "trade_opportunities": int(len(trades)),
        "trades_taken": int((trades["signal"] != 0).sum()),
        "signals_skipped_while_position_open": int(((trades["proposed_signal"] != 0) & (trades["signal"] == 0)).sum()),
        "long_trades": int((trades["signal"] == 1).sum()),
        "short_trades": int((trades["signal"] == -1).sum()),
        "flat_opportunities": int((trades["signal"] == 0).sum()),
        "trade_coverage": float((trades["signal"] != 0).mean()),
        "round_trip_cost_bps": float(round_trip_cost_bps),
        "total_return_net": float(trades["equity"].iloc[-1] - 1.0),
        "max_drawdown": float(trades["drawdown"].min()),
        "win_rate_net": float((active > 0).mean()) if len(active) else None,
        "average_net_return_per_trade": float(active.mean()) if len(active) else None,
        "sharpe_ratio": sharpe,
        "limitations": [
            "Input must contain out-of-sample predictions.",
            "When horizon_minutes is present, new trades are blocked until the prior horizon ends.",
            "Fixed costs approximate fees and slippage; actual costs may differ.",
            "This evaluates supplied underlying-return series, not options P&L.",
            "Sharpe annualization depends on trade frequency and holding period.",
            "Historical performance does not guarantee future results.",
        ],
    }
    return trades, metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True,
                        help="CSV with timestamp,predicted_return,actual_forward_return; optional horizon_minutes.")
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed/backtest"))
    parser.add_argument("--threshold", type=float, default=0.0)
    parser.add_argument("--cost-bps", type=float, default=10.0)
    parser.add_argument("--periods-per-year", type=int, default=252 * 75)
    args = parser.parse_args()
    if not args.input.is_file():
        raise FileNotFoundError(f"Backtest input not found: {args.input}")
    trades, metrics = run_backtest(
        pd.read_csv(args.input), threshold=args.threshold,
        round_trip_cost_bps=args.cost_bps, periods_per_year=args.periods_per_year,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    trades.to_csv(args.output_dir / "backtest_trades.csv", index=False)
    (args.output_dir / "backtest_metrics.json").write_text(
        json.dumps(metrics, indent=2), encoding="utf-8"
    )
    print("Project Alpha — historical trade backtest")
    print(json.dumps(metrics, indent=2))
    print(f"Trade ledger: {args.output_dir / 'backtest_trades.csv'}")
    print(f"Metrics: {args.output_dir / 'backtest_metrics.json'}")


if __name__ == "__main__":
    main()
