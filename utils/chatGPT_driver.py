import openai


class ChatGPTDriver:
    def __init__(self, api_key: str, model: str = "gpt-4"):
        """
        Initializes the ChatGPT API driver.

        :param api_key: Your OpenAI API key.
        :param model: The GPT model to use (default: "gpt-4").
        """
        self.api_key = api_key
        self.model = model
        openai.api_key = api_key  # Set the API key globally

    def send_message(self, message: str, prompt: str, temperature: float = 0.7):
        """
        Sends a message to ChatGPT and retrieves the response.

        :param message: String with news from perplexity.
        :param temperature: Controls response randomness (0.0 = deterministic, 1.0 = creative).
        :return: The response text from ChatGPT.
        """
        messages = [
            {
                "role": "system",
                "content": prompt
            },
            {
                "role": "user",
                "content": message
            }
        ]
        try:
            response = openai.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature
            )

            return response.choices[0].message.content  # Extract response text

        except Exception as e:
            return f"❌ Error communicating with ChatGPT: {str(e)}"
