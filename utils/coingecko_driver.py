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
        params = {"vs_currency": currency, "days": days, "interval": "daily"}

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

    def get_token_name(self, symbol: str):
        """Fetches the full token name from CoinGecko by its symbol, prioritizing well-known tokens."""
        url = f"{self.BASE_URL}/coins/list"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()

            # Find all tokens matching the symbol
            matching_tokens = [coin for coin in data if coin["symbol"].lower() == symbol.lower()]

            if not matching_tokens:
                return f"Token '{symbol}' not found."

            # Prioritize Ethereum if ETH is requested
            for token in matching_tokens:
                if token["id"] == "ethereum":
                    return token["name"]  # Ensures "Ethereum" is returned instead of a bridged version

            # Return the first found token if no special case (like ETH)
            return matching_tokens[0]["name"]

        return "Error fetching data from CoinGecko."


if __name__ == '__main__':
    # Example usage
    fetcher = CryptoPriceFetcher()
    historical_prices = fetcher.get_historical_prices("btc", days=7)
    print(historical_prices)
