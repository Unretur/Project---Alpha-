
import requests

BASE_URL = "https://api.upstox.com/v2"
BASE_URL_V3 = "https://api.upstox.com/v3"


class UpstoxClient:
    def __init__(self, access_token: str):
        if not access_token:
            raise ValueError("Upstox access token is missing.")

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        })

    def get(self, endpoint: str, params: dict | None = None):
        response = self.session.get(
            f"{BASE_URL}{endpoint}",
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def get_v3(self, endpoint: str, params: dict | None = None):
        response = self.session.get(
            f"{BASE_URL_V3}{endpoint}",
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
