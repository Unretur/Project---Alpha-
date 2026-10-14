"""Streamlit dashboard for Project Alpha's research and paper-trading outputs.

Run: python -m streamlit run src/dashboard/app.py
This UI never sends broker orders.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "processed"
PAPER_DIR = DATA_DIR / "paper_trading"
SIGNALS_FILE = PAPER_DIR / "latest_signals.json"
ACCOUNT_FILE = PAPER_DIR / "paper_account.json"
POSITIONS_FILE = PAPER_DIR / "positions.csv"
TRADES_FILE = PAPER_DIR / "closed_trades.csv"
DATASET_FILE = DATA_DIR / "nifty_training_dataset.csv"
METRICS_FILE = DATA_DIR / "model_training_metrics.json"

st.set_page_config(page_title="Project Alpha", page_icon="📈", layout="wide")


def read_json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except (OSError, pd.errors.ParserError, UnicodeDecodeError):
        return pd.DataFrame()


def money(value) -> str:
    try:
        return f"₹{float(value):,.2f}"
    except (TypeError, ValueError):
        return "—"


def normalize_signals(raw) -> list[dict]:
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    if isinstance(raw, dict):
        items = raw.get("signals", raw.get("predictions", []))
        if isinstance(items, list):
            return [item for item in items if isinstance(item, dict)]
        if isinstance(items, dict):
            return [dict(value, horizon=key) for key, value in items.items() if isinstance(value, dict)]
    return []


def run_module(module: str) -> tuple[bool, str]:
    """Run a local Project Alpha module; never executes broker orders."""
    try:
        completed = subprocess.run(
            [sys.executable, "-m", module],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=90,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    output = (completed.stdout or "") + ("\n" + completed.stderr if completed.stderr else "")
    return completed.returncode == 0, output.strip() or f"Exit code: {completed.returncode}"


st.title("📈 Project Alpha")
st.caption("NIFTY research dashboard · Paper simulation only · No broker orders")

signals = normalize_signals(read_json(SIGNALS_FILE))
account = read_json(ACCOUNT_FILE) or {}
positions = read_csv(POSITIONS_FILE)
trades = read_csv(TRADES_FILE)
metrics_report = read_json(METRICS_FILE) or {}

st.subheader("System status")
status_cols = st.columns(3)
status_cols[0].metric("Mode", "PAPER ONLY")
status_cols[1].metric("Open positions", int(account.get("open_positions", len(positions))))
status_cols[2].metric("Closed trades", int(account.get("closed_trades", len(trades))))

latest_market = account.get("latest_market_timestamp", "Unknown")
st.write(f"**Latest market candle (UTC):** {latest_market}")
if not signals:
    st.warning("No readable signal output yet. Generate signals from the sidebar controls.")
else:
    data_fresh = all(s.get("data_fresh", s.get("fresh", False)) is True for s in signals)
    models_eligible = all(s.get("deployment_eligible", s.get("eligible", False)) is True for s in signals)
    if not data_fresh:
        st.warning("Market data is stale. Forecasts are historical research outputs, not live signals.")
    if not models_eligible:
        st.warning("One or more models failed the deployment gate. Automated model-driven entries remain blocked.")

st.subheader("NIFTY forward-return forecasts")
cards = st.columns(3)
for col, horizon in zip(cards, (5, 15, 30)):
    item = next((s for s in signals if int(s.get("horizon_minutes", 0) or 0) == horizon), None)
    with col:
        st.markdown(f"### {horizon}m")
        if item is None:
            st.metric("Predicted return", "Not available")
            st.caption("Generate predictions to populate this card.")
            continue
        value = item.get("predicted_forward_return", item.get("predicted_return", item.get("prediction")))
        try:
            st.metric("Predicted return", f"{float(value) * 100:+.6f}%")
        except (TypeError, ValueError):
            st.metric("Predicted return", "Not available")
        st.write(f"**Proposal:** {item.get('proposed_signal', item.get('proposed_action', 'UNKNOWN'))}")
        st.write(f"**Paper action:** {item.get('paper_action', item.get('action', 'HOLD'))}")
        st.write(f"**Model eligible:** {'Yes' if item.get('deployment_eligible', item.get('eligible', False)) else 'No'}")
        st.write(f"**Data fresh:** {'Yes' if item.get('data_fresh', item.get('fresh', False)) else 'No'}")
        st.caption(str(item.get("status", "STATUS NOT PROVIDED")))

st.divider()
st.subheader("Virtual paper account")
account_cols = st.columns(4)
account_cols[0].metric("Starting capital", money(account.get("initial_cash")))
account_cols[1].metric("Equity", money(account.get("equity_marked_to_market")))
account_cols[2].metric("Realized net P&L", money(account.get("realized_net_pnl")))
try:
    return_pct = float(account["net_return_pct"])
    account_cols[3].metric("Net return", f"{return_pct:+.4f}%")
except (KeyError, TypeError, ValueError):
    account_cols[3].metric("Net return", "—")
st.caption("The current engine uses synthetic fractional NIFTY index exposure and simplified costs; it is not an exchange-accurate futures/options simulator.")

st.sidebar.header("Controls")
st.sidebar.caption("Actions run local Python modules in this project. No broker orders are sent.")
if st.sidebar.button("🔄 Refresh dashboard", use_container_width=True):
    st.rerun()

if st.sidebar.button("Generate research forecasts", use_container_width=True):
    with st.spinner("Running the signal engine…"):
        ok, output = run_module("src.paper_trading.signal_engine")
    (st.sidebar.success if ok else st.sidebar.error)("Signal engine completed." if ok else "Signal engine failed.")
    st.sidebar.code(output or "No output")
    if ok:
        st.rerun()

can_run_paper = bool(signals) and all(
    s.get("execution_allowed", False) is True
    and s.get("data_fresh", False) is True
    and s.get("deployment_eligible", False) is True
    for s in signals
)
if not can_run_paper:
    st.sidebar.warning("Paper entries are blocked until every signal is explicitly execution-allowed, fresh, and deployment-eligible.")
if st.sidebar.button("▶ Run paper simulation cycle", disabled=not can_run_paper, use_container_width=True):
    with st.spinner("Running the paper simulator…"):
        ok, output = run_module("src.paper_trading.paper_engine")
    (st.sidebar.success if ok else st.sidebar.error)("Paper simulator completed." if ok else "Paper simulator failed.")
    st.sidebar.code(output or "No output")
    if ok:
        st.rerun()

with st.expander("Model evaluation (training report)"):
    horizons = metrics_report.get("horizons", {}) if isinstance(metrics_report, dict) else {}
    if not horizons:
        st.info("No training report found. Run python -m src.models.train_model to generate one.")
    else:
        rows = []
        for label, result in horizons.items():
            test = result.get("test_metrics", {})
            zero = result.get("test_zero_return_baseline", {})
            rows.append({
                "Horizon": label,
                "Model": result.get("selected_model", "unknown"),
                "Test MAE": test.get("mae"),
                "Zero baseline MAE": zero.get("mae"),
                "Deployment eligible": result.get("deployment_eligible", False),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
        st.caption("Do not force the eligibility flag. If the model fails the zero-return benchmark, improve the features/target/model and evaluate again.")

left, right = st.columns(2)
with left:
    st.subheader("Open positions")
    if positions.empty:
        st.info("No open positions.")
    else:
        st.dataframe(positions, use_container_width=True)
with right:
    st.subheader("Closed trades")
    if trades.empty:
        st.info("No closed trades yet.")
    else:
        st.dataframe(trades.tail(100), use_container_width=True)

with st.expander("Raw latest signals"):
    st.json(signals if signals else {"status": "No signal file found", "path": str(SIGNALS_FILE)})

st.caption("Research prototype only. A successful code run does not establish predictive edge or profitability.")
