
import requests

from src.config.config import UPSTOX_ALGO_ACCESS_TOKEN


URL = "https://api.upstox.com/v2/news"

# Reliance Industries — a NIFTY 50 constituent.
# First, verify that authenticated news retrieval works.
PARAMS = {
    "category": "instrument_keys",
    "instrument_keys": "NSE_EQ|INE002A01018",
    "page_number": 1,
    "page_size": 10,
}


def main():
    if not UPSTOX_ALGO_ACCESS_TOKEN:
        raise RuntimeError(
            "UPSTOX_ALGO_ACCESS_TOKEN is missing. "
            "Check your .env configuration."
        )

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {UPSTOX_ALGO_ACCESS_TOKEN}",
    }

    response = requests.get(
        URL,
        headers=headers,
        params=PARAMS,
        timeout=30,
    )

    print("HTTP status:", response.status_code)

    if not response.ok:
        print("API error:", response.text[:1000])
        response.raise_for_status()

    payload = response.json()

    print("API status:", payload.get("status"))

    data = payload.get("data", {})
    articles = data.get("NSE_EQ|INE002A01018", [])

    print("Articles returned:", len(articles))

    for index, article in enumerate(articles[:5], start=1):
        print(f"\nArticle {index}")
        print("Headline:", article.get("heading"))
        print("Summary:", article.get("summary"))
        print("Published timestamp:", article.get("published_time"))
        print("Article link:", article.get("article_link"))

    if not articles:
        print(
            "\nNo articles returned for this instrument. "
            "Authentication may still be successful; "
            "we will inspect the response before proceeding."
        )


if __name__ == "__main__":
    main()
