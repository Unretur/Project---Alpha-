"""Local paper-trade simulator. It never connects to a broker."""
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
POSITIONS = ["signal_id", "instrument", "horizon_minutes", "direction", "entry_timestamp", "entry_price", "notional", "quantity", "entry_cost", "model_name"]
TRADES = POSITIONS + ["exit_timestamp", "exit_price", "gross_pnl", "total_cost", "net_pnl", "return_on_notional", "holding_minutes"]

def run_paper_trading(signals: list[dict[str, Any]], market_data: pd.DataFrame, *,
                      state_dir: Path = STATE, initial_cash: float = 100000.0,
                      notional_per_trade: float = 10000.0, cost_bps_per_side: float = 5.0,
                      now: datetime | None = None) -> dict[str, Any]:
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
    state_dir.mkdir(parents=True, exist_ok=True)
    pos_path, trades_path = state_dir / "positions.csv", state_dir / "closed_trades.csv"
    summary_path = state_dir / "paper_account.json"
    positions = pd.read_csv(pos_path).to_dict("records") if pos_path.exists() else []
    trades = pd.read_csv(trades_path).to_dict("records") if trades_path.exists() else []
    done = {str(x["signal_id"]) for x in trades}
    known = done | {str(x["signal_id"]) for x in positions}
    latest_ts = data["timestamp"].max()
    cost_rate = cost_bps_per_side / 10000.0
    remaining, closed_now = [], []

    # Exit at the first observed candle at/after the intended holding horizon.
    for p in positions:
        expiry = pd.Timestamp(p["entry_timestamp"]) + pd.Timedelta(minutes=int(p["horizon_minutes"]))
        possible = data[data["timestamp"] >= expiry]
        if possible.empty:
            remaining.append(p)
            continue
        row = possible.iloc[0]
        sign = 1.0 if p["direction"] == "LONG" else -1.0
        qty, entry, exit_price = float(p["quantity"]), float(p["entry_price"]), float(row["close"])
        gross = sign * (exit_price - entry) * qty
        fees = float(p["entry_cost"]) + abs(exit_price * qty) * cost_rate
        closed = {**p, "exit_timestamp": row["timestamp"].isoformat(), "exit_price": exit_price,
                  "gross_pnl": gross, "total_cost": fees, "net_pnl": gross - fees,
                  "return_on_notional": (gross - fees) / float(p["notional"]),
                  "holding_minutes": (row["timestamp"] - pd.Timestamp(p["entry_timestamp"])).total_seconds() / 60}
        trades.append(closed); done.add(str(p["signal_id"])); closed_now.append(closed)

    open_horizons = {int(p["horizon_minutes"]) for p in remaining}
    price_lookup = {t.isoformat(): float(c) for t, c in zip(data["timestamp"], data["close"])}
    opened = []
    for s in signals:
        sid = str(s.get("signal_id", ""))
        if not sid or sid in known or sid in done or not s.get("execution_allowed", False):
            continue
        direction = str(s.get("paper_action", "")).upper()
        horizon = int(s["horizon_minutes"])
        stamp = pd.to_datetime(s["timestamp"], utc=True, errors="raise").isoformat()
        if direction not in {"LONG", "SHORT"} or horizon <= 0 or horizon in open_horizons or stamp not in price_lookup:
            continue
        price = price_lookup[stamp]
        p = {"signal_id": sid, "instrument": s.get("instrument", "NIFTY 50"),
             "horizon_minutes": horizon, "direction": direction, "entry_timestamp": stamp,
             "entry_price": price, "notional": notional_per_trade, "quantity": notional_per_trade / price,
             "entry_cost": notional_per_trade * cost_rate, "model_name": s.get("model_name", "unknown")}
        remaining.append(p); opened.append(p); known.add(sid); open_horizons.add(horizon)

    pd.DataFrame(remaining, columns=POSITIONS).to_csv(pos_path, index=False)
    trades_df = pd.DataFrame(trades, columns=TRADES)
    trades_df.to_csv(trades_path, index=False)
    realized = float(pd.to_numeric(trades_df["net_pnl"], errors="coerce").fillna(0).sum()) if not trades_df.empty else 0.0
    mark = float(data.iloc[-1]["close"])
    unrealized = sum((1 if p["direction"] == "LONG" else -1) * (mark - float(p["entry_price"])) * float(p["quantity"]) for p in remaining)
    equity = initial_cash + realized + unrealized
    summary = {"updated_at": now_ts.isoformat(), "mode": "PAPER_ONLY_NO_BROKER",
               "latest_market_timestamp": latest_ts.isoformat(), "initial_cash": initial_cash,
               "notional_per_trade": notional_per_trade, "cost_bps_per_side": cost_bps_per_side,
               "open_positions": len(remaining), "closed_trades": len(trades_df),
               "realized_net_pnl": realized, "unrealized_gross_pnl": unrealized,
               "equity_marked_to_market": equity, "net_return_pct": (equity / initial_cash - 1) * 100,
               "opened_this_run": len(opened), "closed_this_run": len(closed_now),
               "notice": "Simulation only; simplified costs; no broker orders are sent."}
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return {"summary": summary, "opened": opened, "closed": closed_now,
            "positions_path": str(pos_path), "trades_path": str(trades_path), "summary_path": str(summary_path)}

def main():
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
    result = run_paper_trading(signals, pd.read_csv(args.dataset), state_dir=args.state_dir,
                               initial_cash=args.initial_cash, notional_per_trade=args.notional_per_trade,
                               cost_bps_per_side=args.cost_bps_per_side)
    print("Project Alpha paper engine — simulation only")
    for key, value in result["summary"].items():
        print(f"{key}: {value}")
    print(f"Positions: {result['positions_path']}\nClosed trades: {result['trades_path']}\nAccount: {result['summary_path']}")

if __name__ == "__main__":
    main()
