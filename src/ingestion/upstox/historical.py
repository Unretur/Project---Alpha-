import pandas as pd 


from src.config.config import UPSTOX_ACCESS_TOKEN
from src.ingestion.upstox.client import UpstoxClient


NIFTY_50_INSTRUMENT_KEY = "NSE_INDEX|Nifty 50"

INTERVAL = 5
TO_DATE = "2026-10-05"
FROM_DATE = "2026-10-04"


client = UpstoxClient(UPSTOX_ACCESS_TOKEN)

endpoint = (
    f"/historical-candle/"
    f"{NIFTY_50_INSTRUMENT_KEY.replace('|', '%7C')}/"
    f"minutes/"
    f"{INTERVAL}/"
    f"{TO_DATE}/"
    f"{FROM_DATE}"
)

print(endpoint)

response = client.get_v3(endpoint)


candles = response["data"]["candles"]

columns = [
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "open_interest",
]

df = pd.DataFrame(candles, columns=columns)
df.to_csv("data/raw/market/nifty50_5m.csv", index=False)

print("Data saved successfully")

df["timestamp"] = pd.to_datetime(df["timestamp"])
df["time_diff"] = df["timestamp"].diff()

print(df["time_diff"].value_counts().head(10))

print("Sorted:", df["timestamp"].is_monotonic_increasing)
print("Duplicate timestamps:", df["timestamp"].duplicated().sum())

print(df.head())



print("Upstox historical client connected")