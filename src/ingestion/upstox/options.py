from src.config.config import UPSTOX_ACCESS_TOKEN
from src.ingestion.upstox.client import UpstoxClient


client = UpstoxClient(UPSTOX_ACCESS_TOKEN)

NIFTY_50_INSTRUMENT_KEY = "NSE_INDEX|Nifty 50"

params = {
    "instrument_key": NIFTY_50_INSTRUMENT_KEY
}

response = client.get("/option/contract", params=params)

contracts = response["data"]

print("Total contracts:", len(contracts))
first_contract = contracts[0]

print("Instrument Key:", first_contract["instrument_key"])
print("Strike Price:", first_contract["strike_price"])
print("Option Type:", first_contract["instrument_type"])
print("Expiry:", first_contract["expiry"])
print("Lot Size:", first_contract["lot_size"])
print("Weekly:", first_contract["weekly"])




print("Upstox options client connected")

price_params = {
    "instrument_key": NIFTY_50_INSTRUMENT_KEY,
    "interval": "I1"
}

price_response = client.get(
    "/market-quote/ohlc",
    params=price_params
)

nifty_data = price_response["data"]

print("NIFTY market data:", nifty_data)

# Current NIFTY price
nifty_price = nifty_data["NSE_INDEX:Nifty 50"]["last_price"]

# Build a map of strikes containing CE and PE
strike_map = {}

for contract in contracts:
    strike = contract["strike_price"]
    option_type = contract["instrument_type"]

    if option_type in ["CE", "PE"]:
        if strike not in strike_map:
            strike_map[strike] = {}

        strike_map[strike][option_type] = contract

# Keep only strikes where BOTH CE and PE exist
valid_strikes = [
    strike
    for strike, options_at_strike in strike_map.items()
    if "CE" in options_at_strike and "PE" in options_at_strike
]

# Find the valid strike closest to NIFTY price
atm_strike = min(
    valid_strikes,
    key=lambda strike: abs(strike - nifty_price)
)

atm_ce = strike_map[atm_strike]["CE"]
atm_pe = strike_map[atm_strike]["PE"]

print("NIFTY Price:", nifty_price)
print("ATM Strike:", atm_strike)

print("ATM CE:", atm_ce["trading_symbol"])
print("ATM CE Key:", atm_ce["instrument_key"])

print("ATM PE:", atm_pe["trading_symbol"])
print("ATM PE Key:", atm_pe["instrument_key"])