import requests

from enum import Enum


class PostsTimeWindow(Enum):
    HOUR = '1h'
    DAILY = '24h'
    WEEKLY = '7d'


class ElfaDriver:
    def __init__(self, base_url: str, api_key: str):
        self.ELFA_URL = base_url
        self.ELFA_API_KEY = api_key

    def get_top_posts(self, asset: str, time_window: PostsTimeWindow = PostsTimeWindow.HOUR, page: int = 1,
                      page_size: int = 10):
        from app import config
        url = f'{self.ELFA_URL}/top-mentions?ticker={asset}&timeWindow={time_window.value}&page={page}&pageSize={page_size}'
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

            return data['data']

        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error occurred: {e}")


if __name__ == '__main__':
    print(get_top_posts('solana', time_window=PostsTimeWindow.WEEKLY))
