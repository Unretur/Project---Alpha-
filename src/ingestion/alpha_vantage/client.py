import requests

from src.config.config import ALPHA_VANTAGE_API_KEY


BASE_URL = "https://www.alphavantage.co/query"


class AlphaVantageClient:
    """Small Alpha Vantage REST client; callers provide the API function parameters."""

    def __init__(self, api_key: str | None = ALPHA_VANTAGE_API_KEY):
        self.session = requests.Session()
        self.api_key = api_key

    def get(self, params: dict | None = None) -> dict:
        if not self.api_key:
            raise ValueError(
                "ALPHA_VANTAGE_API_KEY is missing. Set it in your .env file."
            )

        query_params = {
            **(params or {}),
            "apikey": self.api_key,
        }
        response = self.session.get(
            BASE_URL,
            params=query_params,
            timeout=30,
        )
        response.raise_for_status()

        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Alpha Vantage returned an unexpected response format.")

        api_error = (
            payload.get("Error Message")
            or payload.get("Note")
            or payload.get("Information")
        )
        if api_error:
            raise RuntimeError(f"Alpha Vantage API response: {api_error}")

        return payload
