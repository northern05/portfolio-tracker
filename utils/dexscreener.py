import logging

import requests
import re

from utils.error import DexScreenerDataError, DexScreenerTokenError


def fetch_dexscreener_data(input_data: str):
    """
    Fetches token data from the Dexscreener API using a Raydium URL or a token address.

    Args:
        input_data (str): Either a Raydium pool URL or a token address.

    Returns:
        dict: The parsed JSON data from the Dexscreener API, or None if the request fails.
    """
    if input_data.startswith("http"):
        match = re.search(r"outputMint=([^&]+)", input_data)
        if not match:
            raise DexScreenerDataError("Invalid Raydium URL. Token address not found.")
        token_address = match.group(1)
        if token_address == 'sol':
            match = re.search(r"inputMint=([^&]+)", input_data)
            if not match:
                raise DexScreenerDataError("Invalid Raydium URL. Token address not found.")
            token_address = match.group(1)
    else:
        token_address = input_data
        if token_address == 'sol':
            raise DexScreenerTokenError()

    chain_id = "solana"
    api_url = f"https://api.dexscreener.com/tokens/v1/{chain_id}/{token_address}"

    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        logging.critical(f"Error fetching data from Dexscreener API: {e}")
        raise DexScreenerDataError(f"Error fetching data from Dexscreener API: {e}")


# Example usage
if __name__ == "__main__":
    analytic_data = fetch_dexscreener_data("6ydBLn9Y21a6rp4ktuvyri8TeFX1dr4XyruqD7gspump")[0]
    print(analytic_data)