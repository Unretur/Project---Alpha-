"""Research-only paper signal generation from the trained Project Alpha artifacts.

No broker orders are sent. Models that fail the validation/test zero-return gate
are marked research-only and cannot authorize simulated positions by default.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from src.models.baseline import DATASET_PATH
from src.models.predict_latest import ARTIFACT_DIR, predict_latest

DEFAULT_OUTPUT = Path("data/processed/paper_trading/latest_signals.json")
DEFAULT_LEDGER = Path("data/processed/paper_trading/signal_ledger.csv")


def _direction(predicted_return: float, threshold: float) -> str:
    if predicted_return >= threshold:
        return "LONG"
    if predicted_return <= -threshold:
        return "SHORT"
    return "HOLD"


def generate_paper_signals(
    dataset: pd.DataFrame,
    *,
    artifact_dir: Path = ARTIFACT_DIR,
    threshold: float = 0.0005,
    max_data_age_minutes: float = 15,
    now: datetime | None = None,
    allow_research_models: bool = True,
) -> list[dict[str, Any]]:
    """Create auditable signals; never submit orders or imply profitability."""
    if threshold < 0:
        raise ValueError("threshold must be non-negative.")
    if max_data_age_minutes <= 0:
        raise ValueError("max_data_age_minutes must be positive.")
    if dataset.empty or "timestamp" not in dataset.columns:
        raise ValueError("Dataset must contain at least one timestamped row.")

    timestamps = pd.to_datetime(dataset["timestamp"], utc=True, errors="raise")
    latest_timestamp = timestamps.max()
    current_time = now or datetime.now(timezone.utc)
    current_timestamp = pd.Timestamp(current_time)
    if current_timestamp.tzinfo is None:
        raise ValueError("now must be timezone-aware.")
    age_minutes = max(0.0, (current_timestamp - latest_timestamp).total_seconds() / 60)
    fresh = age_minutes <= max_data_age_minutes

    predictions = predict_latest(
        dataset,
        artifact_dir=artifact_dir,
        allow_research_model=allow_research_models,
    )
    signals: list[dict[str, Any]] = []
    for item in predictions:
        predicted = float(item["predicted_forward_return"])
        proposed = _direction(predicted, threshold)
        eligible = bool(item["deployment_eligible"])
        # Stale inputs or models that failed the benchmark gate must never
        # authorize simulated execution. Keep the proposal for research review.
        executable = bool(fresh and eligible and proposed != "HOLD")
        signals.append({
            "signal_id": f"NIFTY50-{item['horizon_minutes']}m-{item['timestamp']}",
            "instrument": "NIFTY 50",
            "timestamp": item["timestamp"],
            "generated_at": current_timestamp.isoformat(),
            "horizon_minutes": int(item["horizon_minutes"]),
            "predicted_forward_return": predicted,
            "threshold": float(threshold),
            "proposed_signal": proposed,
            "paper_action": proposed if executable else "HOLD",
            "data_timestamp_age_minutes": round(age_minutes, 3),
            "data_fresh": bool(fresh),
            "model_name": item["model_name"],
            "deployment_eligible": eligible,
            "execution_allowed": executable,
            "status": (
                "READY_FOR_PAPER_SIMULATION" if executable
                else "RESEARCH_ONLY_MODEL_INELIGIBLE" if not eligible
                else "STALE_DATA" if not fresh
                else "BELOW_SIGNAL_THRESHOLD"
            ),
            "notice": "Research simulation only. No broker orders are sent; no profitability is implied.",
        })
    return signals


def write_signal_outputs(
    signals: list[dict[str, Any]],
    *,
    output_path: Path = DEFAULT_OUTPUT,
    ledger_path: Path = DEFAULT_LEDGER,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(signals, indent=2), encoding="utf-8")
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    incoming = pd.DataFrame(signals)
    if ledger_path.exists():
        existing = pd.read_csv(ledger_path)
        combined = pd.concat([existing, incoming], ignore_index=True)
    else:
        combined = incoming
    if not combined.empty and "signal_id" in combined:
        combined = combined.drop_duplicates(subset=["signal_id"], keep="last")
    combined.to_csv(ledger_path, index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DATASET_PATH)
    parser.add_argument("--artifact-dir", type=Path, default=ARTIFACT_DIR)
    parser.add_argument("--threshold", type=float, default=0.0005,
                        help="Absolute predicted-return threshold (default: 5 bps; research setting).")
    parser.add_argument("--max-data-age-minutes", type=float, default=15)
    parser.add_argument("--allow-stale-data", action="store_true",
                        help="Generate research proposals from stale data; execution remains disabled.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    args = parser.parse_args()

    if not args.dataset.is_file():
        raise FileNotFoundError(f"Dataset not found: {args.dataset}. Build the aligned dataset and targets first.")
    dataset = pd.read_csv(args.dataset)
    signals = generate_paper_signals(
        dataset,
        artifact_dir=args.artifact_dir,
        threshold=args.threshold,
        max_data_age_minutes=args.max_data_age_minutes,
        allow_research_models=True,
    )
    if args.allow_stale_data:
        # Explicitly research-only override: retain proposed directions, but
        # force execution_allowed false in every output row.
        for signal in signals:
            signal["execution_allowed"] = False
            signal["paper_action"] = "HOLD"
            signal["status"] = "RESEARCH_ONLY_STALE_OVERRIDE"
    write_signal_outputs(signals, output_path=args.output, ledger_path=args.ledger)
    print("Project Alpha — paper signal engine (NO BROKER ORDERS)")
    for signal in signals:
        print(
            f"{signal['horizon_minutes']}m | proposed={signal['proposed_signal']} "
            f"| action={signal['paper_action']} | predicted_return="
            f"{signal['predicted_forward_return']:.8f} | "
            f"fresh={signal['data_fresh']} | eligible={signal['deployment_eligible']} "
            f"| status={signal['status']}"
        )
    print(f"Latest signals: {args.output}")
    print(f"Signal ledger: {args.ledger}")


if __name__ == "__main__":
    main()
