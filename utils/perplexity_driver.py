from openai import OpenAI


class PerplexityDriver:
    def __init__(self, base_url: str, api_key: str):
        self.model = "sonar"
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.prompt = """
        As a cryptocurrency expert, provide the top 5 latest and most relevant news articles about the asset with the cryptocurrency that user asked for. 
        Focus on market trends, regulatory updates, major partnerships, price movements, and technological advancements. 
        Ensure the sources are reputable (e.g., CoinDesk, CoinTelegraph, Decrypt, Bloomberg Crypto, The Block). 
        Summarize each news item concisely with key insights. If available, include the date and source link.
        """

    def chat_without_streaming(self, message):
        messages = [
            {
                "role": "system",
                "content": self.prompt
            },
            {
                "role": "user",
                "content": message
            }
        ]
        # chat completion without streaming
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        return response.choices[0].message.content

    def chat_streaming(self, messages):
        # chat completion with streaming
        response_stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
        )
        for response in response_stream:
            yield response
