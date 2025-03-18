import requests
import datetime


class CryptoPriceFetcher:
    BASE_URL = "https://api.coingecko.com/api/v3"

    def get_historical_prices(self, symbol: str, days: int = 30, currency: str = "usd"):
        """
        Fetch historical price data for a given token using CoinGecko.

        :param symbol: The token symbol (e.g., "BTC" for Bitcoin).
        :param days: Number of past days to retrieve data for.
        :param currency: Quote currency (e.g., "usd").
        :return: List of dictionaries containing date and price.
        """
        # Get CoinGecko ID for the token symbol
        coin_id = self.get_coin_id(symbol)
        if not coin_id:
            return {"error": f"Token '{symbol}' not found"}

        url = f"{self.BASE_URL}/coins/{coin_id}/market_chart"
        params = {"vs_currency": currency, "days": days, "interval": "hourly"}

        response = requests.get(url, params=params)
        if response.status_code != 200:
            return {"error": "Failed to fetch historical data"}

        data = response.json()
        prices = data.get("prices", [])

        # Format response
        historical_data = [
            {"date": datetime.datetime.utcfromtimestamp(price[0] / 1000).strftime("%Y-%m-%d"), "price": price[1]}
            for price in prices
        ]

        return historical_data

    def get_coin_id(self, symbol: str):
        """Fetch CoinGecko's unique ID for a given token symbol."""
        url = f"{self.BASE_URL}/coins/list"
        response = requests.get(url)

        if response.status_code != 200:
            return None

        data = response.json()
        coin = next((c for c in data if c["symbol"].lower() == symbol.lower()), None)

        return coin["id"] if coin else None

    def get_token_name(self, symbol: str, token_id: str):
        """Fetches the full token name from CoinGecko by its symbol, prioritizing well-known tokens."""
        url = f"{self.BASE_URL}/coins/list"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()

            # Find all tokens matching the symbol
            matching_token = [coin for coin in data if coin["symbol"].lower() == symbol.lower() and coin["id"].lower == token_id.lower()]

            if not matching_token:
                return f"Token '{symbol}' not found."

            # Return the first found token if no special case (like ETH)
            return matching_token[0]["name"]

        return "Error fetching data from CoinGecko."

    def get_twitter_from_coingecko(self, token_id):
        url = f"{self.BASE_URL}/coins/{token_id}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            twitter_url = data.get("links", {}).get("twitter_screen_name")

            if twitter_url:
                return f"https://twitter.com/{twitter_url}"
            else:
                return "No Twitter account found."
        else:
            return "Error fetching data."

    def get_similar_tokens(self, symbol: str):
        """Fetches the top 10 most popular tokens similar to the given symbol, sorted by market cap."""
        url = f"{self.BASE_URL}/coins/markets"
        params = {
            "vs_currency": "usd",  # Get market data in USD
            "order": "market_cap_desc",  # Sort by market cap
            "per_page": 250,  # Fetch top 250 coins (increase if needed)
            "page": 1,
            "sparkline": "false"  # No need for sparkline data
        }
        response = requests.get(url, params=params)

        if response.status_code != 200:
            return {"error": "Failed to fetch data from CoinGecko"}

        data = response.json()

        # Filter tokens that match the symbol in name or symbol
        similar_tokens = [
            {
                "token_id": token["id"],
                "name": token["name"],
                "symbol": token["symbol"].upper(),
                "market_cap": token["market_cap"],
                "image_url": token["image"]
            }
            for token in data if symbol.lower() in token["symbol"].lower() or symbol.lower() in token["name"].lower()
        ]

        # Sort by market capitalization and return top 10
        top_similar_tokens = sorted(similar_tokens, key=lambda x: x["market_cap"], reverse=True)[:10]
        return top_similar_tokens


if __name__ == '__main__':
    # Example usage
    fetcher = CryptoPriceFetcher()
    historical_prices = fetcher.get_historical_prices("btc", days=7)
    print(historical_prices)
