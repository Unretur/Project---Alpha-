"""Local paper-trade simulator. It never connects to a broker.

Safety properties:
- Never uses market candles later than the simulation clock.
- Never opens a position from a future/unmatched signal timestamp.
- Never executes signals explicitly marked stale or model-ineligible.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

SIGNALS = Path("data/processed/paper_trading/latest_signals.json")
DATASET = Path("data/processed/nifty_training_dataset.csv")
STATE = Path("data/processed/paper_trading")
POSITIONS = ["signal_id", "instrument", "horizon_minutes", "direction", "entry_timestamp",
             "entry_price", "notional", "quantity", "entry_cost", "model_name", "trading_mode"]
TRADES = POSITIONS + ["exit_timestamp", "exit_price", "gross_pnl", "total_cost",
                      "net_pnl", "return_on_notional", "holding_minutes"]


def run_paper_trading(
    signals: list[dict[str, Any]],
    market_data: pd.DataFrame,
    *,
    state_dir: Path = STATE,
    initial_cash: float = 100000.0,
    notional_per_trade: float = 10000.0,
    cost_bps_per_side: float = 5.0,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Process eligible signals and position exits using only data known by now."""
    if initial_cash <= 0 or notional_per_trade <= 0 or cost_bps_per_side < 0:
        raise ValueError("Cash/notional must be positive and costs cannot be negative.")
    if market_data.empty or not {"timestamp", "close"}.issubset(market_data.columns):
        raise ValueError("Market data must contain timestamp and close columns.")

    data = market_data[["timestamp", "close"]].copy()
    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True, errors="raise")
    data["close"] = pd.to_numeric(data["close"], errors="raise")
    data = data.dropna().sort_values("timestamp").drop_duplicates("timestamp", keep="last")
    if data.empty or (data["close"] <= 0).any():
        raise ValueError("Valid positive close prices are required.")

    now_ts = pd.Timestamp(now or datetime.now(timezone.utc))
    if now_ts.tzinfo is None:
        raise ValueError("now must be timezone-aware.")
    now_ts = now_ts.tz_convert("UTC")

    # Critical look-ahead guard: exclude every candle later than the simulation clock.
    data = data.loc[data["timestamp"] <= now_ts].reset_index(drop=True)
    if data.empty:
        raise ValueError("No market candles are available at or before the simulation time.")

    state_dir.mkdir(parents=True, exist_ok=True)
    pos_path, trades_path = state_dir / "positions.csv", state_dir / "closed_trades.csv"
    summary_path = state_dir / "paper_account.json"
    positions = pd.read_csv(pos_path).to_dict("records") if pos_path.exists() else []
    trades = pd.read_csv(trades_path).to_dict("records") if trades_path.exists() else []
    done = {str(x["signal_id"]) for x in trades}
    known = done | {str(x["signal_id"]) for x in positions}
    latest_ts = data["timestamp"].max()
    cost_rate = cost_bps_per_side / 10000.0
    remaining: list[dict[str, Any]] = []
    closed_now: list[dict[str, Any]] = []

    # Only candles already visible at now can be used to close a position.
    for position in positions:
        entry_ts = pd.to_datetime(position["entry_timestamp"], utc=True, errors="raise")
        expiry = entry_ts + pd.Timedelta(minutes=int(position["horizon_minutes"]))
        possible = data.loc[data["timestamp"] >= expiry]
        if possible.empty:
            remaining.append(position)
            continue

        row = possible.iloc[0]
        sign = 1.0 if position["direction"] == "LONG" else -1.0
        qty = float(position["quantity"])
        entry = float(position["entry_price"])
        exit_price = float(row["close"])
        gross = sign * (exit_price - entry) * qty
        fees = float(position["entry_cost"]) + abs(exit_price * qty) * cost_rate
        closed = {
            **position,
            "exit_timestamp": row["timestamp"].isoformat(),
            "exit_price": exit_price,
            "gross_pnl": gross,
            "total_cost": fees,
            "net_pnl": gross - fees,
            "return_on_notional": (gross - fees) / float(position["notional"]),
            "holding_minutes": (row["timestamp"] - entry_ts).total_seconds() / 60,
        }
        trades.append(closed)
        done.add(str(position["signal_id"]))
        closed_now.append(closed)

    open_horizons = {int(p["horizon_minutes"]) for p in remaining}
    price_lookup = {t.isoformat(): float(c) for t, c in zip(data["timestamp"], data["close"])}
    opened: list[dict[str, Any]] = []

    for signal in signals:
        signal_id = str(signal.get("signal_id", ""))
        if not signal_id or signal_id in known or signal_id in done:
            continue
        research_mode = signal.get("trading_mode") == "RESEARCH_PAPER"
        if research_mode:
            # Experimental paper trades may use an ineligible model, but only
            # with an explicit research flag and fresh data. No broker is involved.
            if signal.get("research_trade_allowed") is not True:
                continue
            if signal.get("data_fresh") is not True:
                continue
            direction = str(signal.get("proposed_signal", "")).upper()
        else:
            if not bool(signal.get("execution_allowed", False)):
                continue
            # Defence in depth: unsafe flags cannot be overridden by execution_allowed.
            if signal.get("data_fresh") is False or signal.get("deployment_eligible") is False:
                continue
            direction = str(signal.get("paper_action", "")).upper()
        try:
            horizon = int(signal["horizon_minutes"])
            stamp = pd.to_datetime(signal["timestamp"], utc=True, errors="raise").isoformat()
        except (KeyError, TypeError, ValueError):
            continue
        if direction not in {"LONG", "SHORT"} or horizon <= 0 or horizon in open_horizons:
            continue
        # This exact lookup also rejects timestamps in the future or candles not in this dataset.
        if stamp not in price_lookup:
            continue

        price = price_lookup[stamp]
        position = {
            "signal_id": signal_id,
            "instrument": signal.get("instrument", "NIFTY 50"),
            "horizon_minutes": horizon,
            "direction": direction,
            "entry_timestamp": stamp,
            "entry_price": price,
            "notional": notional_per_trade,
            "quantity": notional_per_trade / price,
            "entry_cost": notional_per_trade * cost_rate,
            "model_name": signal.get("model_name", "unknown"),
            "trading_mode": "RESEARCH_PAPER" if research_mode else "DEPLOYMENT_APPROVED",
        }
        remaining.append(position)
        opened.append(position)
        known.add(signal_id)
        open_horizons.add(horizon)

    pd.DataFrame(remaining, columns=POSITIONS).to_csv(pos_path, index=False)
    trades_df = pd.DataFrame(trades, columns=TRADES)
    trades_df.to_csv(trades_path, index=False)

    realized = float(pd.to_numeric(trades_df["net_pnl"], errors="coerce").fillna(0).sum()) if not trades_df.empty else 0.0
    mark = float(data.iloc[-1]["close"])
    unrealized = sum(
        (1 if p["direction"] == "LONG" else -1)
        * (mark - float(p["entry_price"])) * float(p["quantity"])
        for p in remaining
    )
    equity = initial_cash + realized + unrealized
    summary = {
        "updated_at": now_ts.isoformat(),
        "mode": "PAPER_ONLY_NO_BROKER",
        "research_mode_trades": sum(1 for p in remaining if p.get("trading_mode") == "RESEARCH_PAPER") + sum(1 for t in trades if t.get("trading_mode") == "RESEARCH_PAPER"),
        "latest_market_timestamp": latest_ts.isoformat(),
        "simulation_clock": now_ts.isoformat(),
        "initial_cash": initial_cash,
        "notional_per_trade": notional_per_trade,
        "cost_bps_per_side": cost_bps_per_side,
        "open_positions": len(remaining),
        "closed_trades": len(trades_df),
        "realized_net_pnl": realized,
        "unrealized_gross_pnl": unrealized,
        "equity_marked_to_market": equity,
        "net_return_pct": (equity / initial_cash - 1) * 100,
        "opened_this_run": len(opened),
        "closed_this_run": len(closed_now),
        "notice": "Simulation only; synthetic fractional index exposure and simplified costs; no broker orders are sent.",
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return {
        "summary": summary,
        "opened": opened,
        "closed": closed_now,
        "positions_path": str(pos_path),
        "trades_path": str(trades_path),
        "summary_path": str(summary_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--signals", type=Path, default=SIGNALS)
    parser.add_argument("--dataset", type=Path, default=DATASET)
    parser.add_argument("--state-dir", type=Path, default=STATE)
    parser.add_argument("--initial-cash", type=float, default=100000.0)
    parser.add_argument("--notional-per-trade", type=float, default=10000.0)
    parser.add_argument("--cost-bps-per-side", type=float, default=5.0)
    args = parser.parse_args()
    if not args.signals.is_file() or not args.dataset.is_file():
        raise FileNotFoundError("Run the data pipeline and signal engine before paper trading.")
    signals = json.loads(args.signals.read_text(encoding="utf-8"))
    if not isinstance(signals, list):
        raise ValueError("Signal file must contain a JSON list of signal objects.")
    result = run_paper_trading(
        signals, pd.read_csv(args.dataset), state_dir=args.state_dir,
        initial_cash=args.initial_cash, notional_per_trade=args.notional_per_trade,
        cost_bps_per_side=args.cost_bps_per_side,
    )
    print("Project Alpha paper engine — simulation only")
    for key, value in result["summary"].items():
        print(f"{key}: {value}")
    print(f"Positions: {result['positions_path']}\nClosed trades: {result['trades_path']}\nAccount: {result['summary_path']}")


if __name__ == "__main__":
    main()
