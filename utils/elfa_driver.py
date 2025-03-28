import re
import requests


class ElfaDriver:
    def __init__(self, base_url: str, api_key: str):
        self.ELFA_URL = base_url
        self.ELFA_API_KEY = api_key

    def is_valid_ticker(self, post_text, symbol):
        """Check if the symbol is referenced correctly."""
        pattern = rf"\b{symbol}\b"  # Ensure it's a standalone word
        return bool(re.search(pattern, post_text, re.IGNORECASE))

    def get_squeeze(self, symbol: str):
        all_tickers = [f"${symbol}", f"%23{symbol}", symbol]
        tweets = []
        for ticker in all_tickers:
            result = self.get_top_posts(symbol=ticker)
            tweets.extend(result)

        # Remove duplicates based on 'content'
        unique_tweets = {tweet["content"]: tweet for tweet in tweets}.values()
        # Filter tweets that match the symbol criteria
        filtered_tweets = [tweet for tweet in unique_tweets if self.is_valid_ticker(tweet["content"], symbol)]

        return filtered_tweets

    def get_top_posts(self, symbol: str, time_window: str = "2d", page: int = 1,
                      page_size: int = 25):
        url = f'{self.ELFA_URL}/top-mentions?ticker={symbol}&timeWindow={time_window}&page={page}&pageSize={page_size}'
        headers = {
            'x-elfa-api-key': self.ELFA_API_KEY
        }

        try:
            response = requests.get(url, headers=headers)

            if response.status_code == 400:
                error_data = response.json()
                raise Exception(
                    f"Bad Request: code: {error_data.get('code', 'Unknown')} "
                    f"message: {error_data.get('message', 'No message provided')} "
                    f"details: {error_data.get('details', 'No details provided')}"
                )
            elif response.status_code == 401:
                error_data = response.json()
                raise Exception(
                    f"Unauthorized: code: {error_data.get('code', 'Unknown')} "
                    f"message: {error_data.get('message', 'No message provided')}"
                )
            elif response.status_code == 500:
                error_data = response.json()
                raise Exception(
                    f"Internal Server Error: code: {error_data.get('code', 'Unknown')} "
                    f"message: {error_data.get('message', 'No message provided')} "
                    f"details: {error_data.get('details', 'No details provided')}"
                )

            response.raise_for_status()

            data = response.json()

            if not data.get('success', True):
                raise Exception(f"API returned an error: {data.get('message', 'Unknown error')}")

            return data['data']['data']

        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error occurred: {e}")


if __name__ == '__main__':
    elfa = ElfaDriver(base_url="https://api.elfa.ai/v1", api_key="elfak_db1eb0fe5cadbee7f798e2f79f5c53b8bfddb7d5")
    print(elfa.get_squeeze(symbol="MKR"))
