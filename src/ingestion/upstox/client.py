import requests

from src.config.config import UPSTOX_ACCESS_TOKEN


BASE_URL = "https://api.upstox.com/v2"


class UpstoxClient:
    def __init__(self, access_token: str):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            }
        )

    def get(self, endpoint: str, params: dict | None = None):
        url = f"{BASE_URL}{endpoint}"

        response = self.session.get(
            url,
            params=params,
            timeout=30,
        )

        response.raise_for_status()

        return response.json()
    
    def get(self, endpoint: str, params: dict | None = None):
        url = f"{BASE_URL}{endpoint}"

        response = self.session.get(
            url,
            params=params,
            timeout=30,
        )

        response.raise_for_status()

        return response.json()

    def get_v3(self, endpoint: str, params: dict | None = None):
        url = f"https://api.upstox.com/v3{endpoint}"

        response = self.session.get(
            url,
            params=params,
            timeout=30,
        )

        response.raise_for_status()

        return response.json()


client = UpstoxClient(UPSTOX_ACCESS_TOKEN)













client = UpstoxClient(UPSTOX_ACCESS_TOKEN)


