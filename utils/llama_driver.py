import requests
import openai


class LlamaDriver:
    def __init__(self, base_url: str):
        """
        Initializes the ChatGPT API driver.
        """
        self.BASE_URL = base_url
        self.analize_prompt = """
            I have collected the top {X} posts from ELFA related to cryptocurrency discussions. 
            Each post includes text content, engagement metrics (likes, comments, shares), and timestamps. 
            Please analyze  and return these posts based on the following criteria:
            """
        self.bullish = """1. #### *Top Bullish Post:*
                - Identify the most engaging bullish post (highest likes/comments/shares) that reflects strong positive sentiment.
                Don't make summarizing and drop any summarizing if exists.
                Highlight text headings according to telegram's Markdown with *."""
        self.fud = """2. #### **Top FUD/Negative Post:**
                - Identify the most engaging FUD/negative post that reflects concerns, fear, or uncertainty.
                Don't make summarizing and drop any summarizing if exists.
                Highlight text headings according to telegram's Markdown with *."""


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

    def get_bullish_fud(self, symbol: str, post_data: dict):
        result = {}
        message = f"""Parse X posts which i add in posts data with ${symbol.upper()}.
                Posts data: {post_data}
                Don't use "Based on your provided data, here is the requested analysis:"
                don't use the description of the analysis method
                Don't make summarizing and drop any summarizing if exists.
                don't add Note or another comments, only twitter posts
                RETURN as a template:"""

        data = {"prompt": f"{self.analize_prompt} {self.bullish}", "msg": message}
        response = requests.post(url=self.BASE_URL, json=data)
        if response.status_code == 200:
            bullish = {"bullish": response.json().get("response")}
        else:
            bullish = {"error": "error result"}
        result.update({"bullish": bullish})

        data = {"prompt": f"{self.analize_prompt} {self.fud}", "msg": message}
        response = requests.post(url=self.BASE_URL, json=data)
        if response.status_code == 200:
            fud = {"bullish": response.json().get("response")}
        else:
            fud = {"error": "error result"}
        result.update({"bullish": fud})
        return result