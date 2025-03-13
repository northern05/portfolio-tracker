import requests


class GrokDriver:
    def __init__(self, api_key: str, base_url: str):
        """
        Initializes the Grok API driver.

        :param api_key: Your Grok API key.
        :param base_url: The base API URL for Grok (default is hypothetical).
        """
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def send_message(self, messages: list, temperature: float = 0.7, max_tokens: int = 500):
        """
        Sends a message to Grok and retrieves the response.

        :param messages: A list of dicts containing past conversation history.
        :param temperature: Controls response randomness (0.0 = deterministic, 1.0 = creative).
        :param max_tokens: Maximum tokens to generate in response.
        :return: The response text from Grok.
        """
        try:
            url = f"{self.base_url}/chat/completions"
            payload = {
                "model": "grok-1",
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()  # Raise an error for HTTP issues

            return response.json()["choices"][0]["message"]["content"]  # Extract response text

        except requests.exceptions.RequestException as e:
            return f"❌ Error communicating with Grok: {str(e)}"

    def format_message(self, role: str, content: str):
        """
        Formats a message into Grok's expected structure.

        :param role: The role of the message sender ("system", "user", or "assistant").
        :param content: The message content.
        :return: A properly formatted message dictionary.
        """
        return {"role": role, "content": content}