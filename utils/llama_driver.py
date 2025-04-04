import requests
from pydantic import BaseModel

twitter_post_types = ("bullish", "fud")

class AnswerFormat(BaseModel):
    twitter_user_id: str
    twitter_id: str

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
        message = f"Token Ticker: ${symbol.upper()} \n Type of witter post to be returned: ${twitt_type.upper()} \nPosts: {post_data}"

        data = {"prompt": prompt, "msg": message, "response_format": {"type": "json_schema", "json_schema": {"schema": AnswerFormat.model_json_schema()},
    },}
        response = requests.post(url=self.BASE_URL, json=data)
        if response.status_code == 200:
            twitt = response.json().get("response").removesuffix("</s>").replace('\n', ' \n ')
        else:
            twitt = "error result"
        return twitt
