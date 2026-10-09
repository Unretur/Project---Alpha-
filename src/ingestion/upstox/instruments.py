from src.config.config import UPSTOX_ACCESS_TOKEN
from src.ingestion.upstox.client import UpstoxClient


def find_nifty50():
    if not UPSTOX_ACCESS_TOKEN:
        raise ValueError("UPSTOX_ACCESS_TOKEN is missing. Check your .env file.")

    client = UpstoxClient(UPSTOX_ACCESS_TOKEN)
    params = {
        "query": "NIFTY",
        "exchanges": "NSE",
        "segments": "INDEX",
        "page_number": 1,
        "records": 20,
    }

    return client.get("/instruments/search", params=params)


if __name__ == "__main__":
    result = find_nifty50()

    for instrument in result["data"]:
        print("Name:", instrument.get("name"))
        print("Exchange:", instrument.get("exchange"))
        print("Trading Symbol:", instrument.get("trading_symbol"))
        print("Instrument Key:", instrument.get("instrument_key"))
        print("Instrument Type:", instrument.get("instrument_type"))
        print("-" * 50)