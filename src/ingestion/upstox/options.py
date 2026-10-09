from datetime import date
from typing import Any

from src.config.config import UPSTOX_ACCESS_TOKEN
from src.ingestion.upstox.client import UpstoxClient


NIFTY_50_INSTRUMENT_KEY = "NSE_INDEX|Nifty 50"


def _parse_expiry(value: Any) -> date | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _is_weekly(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    if isinstance(value, (int, float)):
        return value == 1
    return False


def select_atm_call_put(
    contracts: list[dict],
    nifty_price: float,
    as_of_date: date | None = None,
) -> tuple[dict, dict]:
    """Select a CE/PE pair at the closest strike for the nearest eligible weekly expiry."""
    if not contracts:
        raise ValueError("Upstox returned no option contracts.")
    if nifty_price <= 0:
        raise ValueError("NIFTY price must be greater than zero.")

    decision_date = as_of_date or date.today()
    eligible: list[tuple[date, dict]] = []
    saw_expiry = False
    saw_weekly_flag = False

    for contract in contracts:
        expiry = _parse_expiry(contract.get("expiry"))
        if expiry is None:
            continue
        saw_expiry = True
        if expiry < decision_date:
            continue
        if "weekly" in contract:
            saw_weekly_flag = True
            if not _is_weekly(contract.get("weekly")):
                continue
        eligible.append((expiry, contract))

    if not saw_expiry:
        raise ValueError("Option contract response does not contain valid expiry dates.")
    if saw_weekly_flag and not eligible:
        raise ValueError("No unexpired weekly option contracts are available.")
    if not eligible:
        raise ValueError("No unexpired option contracts are available.")

    # Never mix strikes from different expiries in one CE/PE pair.
    nearest_expiry = min(expiry for expiry, _ in eligible)
    expiry_contracts = [
        contract for expiry, contract in eligible if expiry == nearest_expiry
    ]

    strike_map: dict[float, dict[str, dict]] = {}
    for contract in expiry_contracts:
        try:
            strike = float(contract["strike_price"])
            option_type = contract["instrument_type"]
        except (KeyError, TypeError, ValueError):
            continue

        if option_type in ("CE", "PE"):
            strike_map.setdefault(strike, {})[option_type] = contract

    valid_strikes = [
        strike for strike, options in strike_map.items()
        if "CE" in options and "PE" in options
    ]
    if not valid_strikes:
        raise ValueError(
            f"No CE/PE pair is available for expiry {nearest_expiry.isoformat()}."
        )

    atm_strike = min(valid_strikes, key=lambda strike: abs(strike - nifty_price))
    return strike_map[atm_strike]["CE"], strike_map[atm_strike]["PE"]


def main() -> None:
    if not UPSTOX_ACCESS_TOKEN:
        raise ValueError("UPSTOX_ACCESS_TOKEN is missing. Check your .env file.")

    client = UpstoxClient(UPSTOX_ACCESS_TOKEN)

    response = client.get(
        "/option/contract",
        params={"instrument_key": NIFTY_50_INSTRUMENT_KEY},
    )
    contracts = response.get("data") or []
    print("Total contracts:", len(contracts))

    price_response = client.get(
        "/market-quote/ohlc",
        params={
            "instrument_key": NIFTY_50_INSTRUMENT_KEY,
            "interval": "I1",
        },
    )
    nifty_data = price_response.get("data") or {}
    quote = nifty_data.get("NSE_INDEX:Nifty 50")
    if not quote or quote.get("last_price") is None:
        raise ValueError("NIFTY quote is missing from the Upstox response.")

    nifty_price = float(quote["last_price"])
    atm_ce, atm_pe = select_atm_call_put(contracts, nifty_price)

    print("Upstox options client connected")
    print("NIFTY Price:", nifty_price)
    print("Expiry:", atm_ce["expiry"])
    print("ATM Strike:", atm_ce["strike_price"])
    print("ATM CE:", atm_ce.get("trading_symbol"))
    print("ATM CE Key:", atm_ce.get("instrument_key"))
    print("ATM PE:", atm_pe.get("trading_symbol"))
    print("ATM PE Key:", atm_pe.get("instrument_key"))


if __name__ == "__main__":
    main()
