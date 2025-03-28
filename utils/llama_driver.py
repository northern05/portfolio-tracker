import requests

twitter_post_types = ("bullish", "fud")


class LlamaDriver:
    def __init__(self, base_url: str):
        """
        Initializes the ChatGPT API driver.
        """
        self.BASE_URL = base_url

    def send_message(self, message: str, prompt: str):
        """
        Sends a message to ChatGPT and retrieves the response.

        :param message: String with news from perplexity.
        :param prompt: Controls response randomness (0.0 = deterministic, 1.0 = creative).
        :return: The response text from ChatGPT.
        """
        data = {"prompt": prompt, "msg": message}
        response = requests.post(url="http://195.189.60.154:8000/generate", json=data)
        if response.status_code == 200:
            return response.json().get("response")
        else:
            return None

    def get_bullish_fud(self, symbol: str, post_data: dict, prompt: str, twitt_type: str):
        message = f"""Parse X posts with ${symbol.upper()}.
                Posts data: {post_data}
                Return TOP 1 {twitt_type.upper()} post data about {symbol.upper()} 'twitter_id' and 'twitter_user_id' of this post in JSON format.
                (use engagement metrics to pick up the post from the {twitt_type.upper()} ones):""" + \
                """###Output format
                {"twitter_user_id": <twitter_user_id>, "twitter_id": <twitter_id>}
                ###########################################"""

        data = {"prompt": prompt, "msg": message}
        response = requests.post(url=self.BASE_URL, json=data)
        if response.status_code == 200:
            twitt = response.json().get("response").removesuffix("</s>").replace('\n', ' \n ')
        else:
            twitt = "error result"
        return twitt
