import requests


def fetch_solana_price_binance() -> float:
    url = "https://api.binance.com/api/v3/ticker/price"
    params = {
        "symbol": "SOLUSDT"
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    return float(data.get("price"))

if __name__ == "__main__":
    price = fetch_solana_price_binance()
    print(f"Solana price in USDT (Binance): {price}")