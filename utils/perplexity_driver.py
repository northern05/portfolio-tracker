from openai import OpenAI


class PerplexityDriver:
    def __init__(self, base_url: str, api_key: str):
        self.model = "sonar-deep-research"
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def chat_without_streaming(self, messages):
        # chat completion without streaming
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        return response

    def chat_streaming(self, messages):
        # chat completion with streaming
        response_stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
        )
        for response in response_stream:
            yield response
