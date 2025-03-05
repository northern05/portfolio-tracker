import requests


class CoinMarketCapDriver:
    def __init__(self, base_url: str, api_key: str):
        self.API_KEY = api_key
        self.BASE_URL = base_url
        self.headers = {
            "Accepts": "application/json",
            "X-CMC_PRO_API_KEY": self.API_KEY
        }

    def get_similar_tokens(self, symbol: str):
        """Fetches tokens similar to the given symbol from CoinMarketCap API."""
        url = f"{self.BASE_URL}/map"  # Endpoint to fetch all token mappings
        response = requests.get(url, headers=self.headers)

        if response.status_code != 200:
            return {"error": "Failed to fetch data from CoinMarketCap"}

        data = response.json().get("data", [])

        # Filter tokens that have the entered symbol as a substring (case-insensitive)
        similar_tokens = [
            {
                "name": token["name"],
                "symbol": token["symbol"],
                "image_url": f"https://s2.coinmarketcap.com/static/img/coins/64x64/{token['id']}.png"
                # CMC image URL pattern
            }
            for token in data if symbol.lower() in token["symbol"].lower()
        ]

        return similar_tokens


if __name__ == '__main__':
    # Example Usage:
    cmc_driver = CoinMarketCapDriver()
    result = cmc_driver.get_similar_tokens("BTC")
    print(result)
