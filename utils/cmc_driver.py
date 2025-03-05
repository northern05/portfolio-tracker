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

    def get_current_token_price(self, symbol: str):
        """Fetches the current price of a given token by its symbol."""

        # Step 1: Get token ID from symbol
        url = f"{self.BASE_URL}/map"
        response = requests.get(url, headers=self.headers)

        if response.status_code != 200:
            return {"error": "Failed to fetch token data"}

        data = response.json().get("data", [])

        # Find the exact match for the token symbol
        token = next((t for t in data if t["symbol"].upper() == symbol.upper()), None)

        if not token:
            return {"error": f"Token '{symbol}' not found"}

        token_id = token["id"]

        # Step 2: Fetch the token's price
        price_url = f"{self.BASE_URL}/quotes/latest?id={token_id}"
        price_response = requests.get(price_url, headers=self.headers)

        if price_response.status_code != 200:
            return {"error": "Failed to fetch token price"}

        price_data = price_response.json().get("data", {}).get(str(token_id), {})
        price_usd = price_data.get("quote", {}).get("USD", {}).get("price", "N/A")

        return {
            "name": token["name"],
            "symbol": token["symbol"],
            "price_usd": price_usd
        }


if __name__ == '__main__':
    # Example Usage:
    cmc_driver = CoinMarketCapDriver()
    result = cmc_driver.get_similar_tokens("BTC")
    print(result)
