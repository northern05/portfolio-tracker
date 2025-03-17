from datetime import datetime, timedelta
from openai import OpenAI


class PerplexityDriver:
    def __init__(self, base_url: str, api_key: str):
        self.model = "sonar-pro"
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def chat_without_streaming(self, symbol: str | list, full_token_name: str, twitter: str):
        message = f"""
                1. Find News about {symbol} from {datetime.now() - timedelta(days=7)} to {datetime.now()}
                2. search for News about price moves without any predictions
                3. **search for News about investment landscape and ecosystem updates**
                4. **all this (news and prices) should be drawn up in the form of a template report and duplicates should be removed**
                """
        prompt = f"""
                1. retrieve news about the crypto asset "${symbol}" or "{full_token_name}" focusing on events that occurred between 03.03.2025 and 11.03.2025. 
                Ensure the target the event occurrence dates (not the publication dates). 
                Include language-agnostic keywords since all languages should be accepted (non-English articles will later be translated to English).
                2. **Find news articles about past price movements:
                - within 03.03.2025 and 11.03.2025 date range
                - excluding any predictions or forecasts
                - show me all links when you get information**
                3. **Find news articles about investment landscape and ecosystem updates:
                - within 03.03.2025 and 11.03.2025 date range
                - show me all links when you get information** 
                
                highlight text headings according to telegram's markdown with
                Don't use phrases "Based on your provided data, here is the requested analysis:", "Here is a template report summarizing" etc.
                Highlight text headings according to telegram's markdown with** **
                don't use the description of the analysis method
                Don't make summarizing and drop any summarizing if exists.
                Add numbers to core paragraphs.      
                Get only real news, don't generate it from yourself.
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
