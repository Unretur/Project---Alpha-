import requests

from src.config.config import FRED_API_KEY


BASE_URL = "https://api.stlouisfed.org/fred"


class FREDClient:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError(
                "FRED_API_KEY is missing. Set it in your .env file."
            )
        self.session = requests.Session()
        self.api_key = api_key

    def get(self, endpoint: str, params: dict | None = None):
        params = {
            **(params or {}),
            "api_key": self.api_key,
            "file_type": "json",
        }

        if not self.api_key:
            raise ValueError(
                "FRED_API_KEY is missing. Set it in your .env file."
            )

        response = self.session.get(
            f"{BASE_URL}{endpoint}",
            params=params,
            timeout=30,
        )

        response.raise_for_status()

        return response.json()


client = FREDClient(FRED_API_KEY)