from openai import OpenAI


class PerplexityDriver:
    def __init__(self, base_url: str, api_key: str):
        self.model = "sonar-pro"
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def chat_without_streaming(self, symbol: str, full_token_name: str):
        message = """
        1. Generate a Report by this template based on News provided below
            1. Name: News Report
            2. Price Moves
                1. News and Link
            3. Ecosystem Updates & Partnerships
                1. News and Link
            4. Investment Landscape
                1. News and Link
        2. News Data: Output from 1st Prompt
        """
        prompt = f"""
        retrieve news about the crypto asset "${symbol}" or "{full_token_name}" focusing on events that occurred between 03.03.2025 and 11.03.2025. 
        Ensure the target the event occurrence dates (not the publication dates). 
        Include language-agnostic keywords since all languages should be accepted (non-English articles will later be translated to English).
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
