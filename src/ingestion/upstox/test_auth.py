
import requests

from src.config.config import UPSTOX_ALGO_ACCESS_TOKEN


def main():
    if not UPSTOX_ALGO_ACCESS_TOKEN:
        raise RuntimeError("Access token is missing.")

    response = requests.get(
        "https://api.upstox.com/v2/user/profile",
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {UPSTOX_ALGO_ACCESS_TOKEN}",
        },
        timeout=30,
    )

    print("HTTP status:", response.status_code)

    if response.ok:
        print("Authentication successful.")
    else:
        print("Authentication failed.")
        print("Response:", response.text[:500])


if __name__ == "__main__":
    main()
