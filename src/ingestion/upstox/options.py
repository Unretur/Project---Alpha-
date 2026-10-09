from src.config.config import UPSTOX_ACCESS_TOKEN
from src.ingestion.upstox.client import UpstoxClient


NIFTY_50_INSTRUMENT_KEY = "NSE_INDEX|Nifty 50"


def select_atm_call_put(contracts: list[dict], nifty_price: float) -> tuple[dict, dict]:
    """Return the closest strike for which both CE and PE contracts exist."""
    if not contracts:
        raise ValueError("Upstox returned no option contracts.")

    strike_map: dict[float, dict[str, dict]] = {}
    for contract in contracts:
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
        raise ValueError("No strike has both a CE and a PE contract.")

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
    print("ATM Strike:", atm_ce["strike_price"])
    print("ATM CE:", atm_ce.get("trading_symbol"))
    print("ATM CE Key:", atm_ce.get("instrument_key"))
    print("ATM PE:", atm_pe.get("trading_symbol"))
    print("ATM PE Key:", atm_pe.get("instrument_key"))


if __name__ == "__main__":
    main()
