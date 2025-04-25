import json
import time
import requests
from pydantic import BaseModel

twitter_post_types = ("bullish", "fud")


class AnswerFormat(BaseModel):
    twitter_user_id: str
    twitter_id: str


class LlamaDriver:
    def __init__(self, llama_url: str, mistral_url: str):
        """
        Initializes the ChatGPT API driver.
        """
        self.MISTRAL = mistral_url
        self.BASE_LLAMA_URL = llama_url

    def send_message(self, message: str, prompt: str):
        """
        Sends a message to ChatGPT and retrieves the response.

        :param message: String with news from perplexity.
        :param prompt: Controls response randomness (0.0 = deterministic, 1.0 = creative).
        :return: The response text from ChatGPT.
        """
        # for attempt in range(max_retries):
        #     err_str = "[0_system]"
        #     data = {"prompt": prompt, "msg": message}
        #     response = requests.post(url="http://195.189.60.154:8000/generate", json=data)
        #     if response.status_code == 200:
        #         llm_result = response.json().get("response")
        #         if err_str in llm_result:
        #             time.sleep(1)
        #             continue
        #         else:
        #             return llm_result
        data = {"messages": [{"role": "system", "content": prompt},
                             {"role": "user", "content": message}]}
        response = requests.post(url=self.MISTRAL, json=data)
        if response.status_code == 200:
            llm_result = response.json().get("choices")[0].get("message").get("content")
            return llm_result

    def bullish_fud(self, message: str, prompt: str):
        data = {"prompt": prompt, "msg": message}
        response = requests.post(url=self.BASE_LLAMA_URL, json=data)
        if response.status_code == 200:
            llm_result = response.json().get("response")
            return llm_result
