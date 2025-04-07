from datetime import datetime, timedelta
from openai import OpenAI


class PerplexityDriver:
    def __init__(self, base_url: str, api_key: str):
        self.model = "sonar-pro"
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def chat_without_streaming(self, message: str, prompt: str):
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
            web_search_options={"search_context_size": "high"}
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

if __name__ == '__main__':
    driver = PerplexityDriver(base_url="https://api.perplexity.ai", api_key="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")
    # symbols = [{"full_token_name":"MakerDAO", "twitter":"https://twitter.com/SkyEcosystem","symbol":"MKR"},
    #            {"full_token_name":"APTOS", "twitter":"https://x.com/Aptos_Network","symbol":"APT"},
    #            {"full_token_name":"SOLANA", "twitter":"https://twitter.com/solana","symbol":"SOL"},
    #            {"full_token_name":"SUI", "twitter":"https://twitter.com/SuiNetwork","symbol":"SUI"},
    #            {"full_token_name":"aerodrome-finance", "twitter":"https://x.com/aerodromefi","symbol":"AERO"},
    #            {"full_token_name":"ssv-network", "twitter":"https://x.com/ssv_network","symbol":"SSV"},
    #            {"full_token_name":"ethereum", "twitter":"https://twitter.com/ethereum","symbol":"ETH"},
    #            {"full_token_name":"ondo-finance", "twitter":"https://twitter.com/OndoFinance","symbol":"ONDO"},
    #            {"full_token_name":"arc", "twitter":"https://x.com/ARCreactorAI","symbol":"ARC"},
    #            {"full_token_name":"virtual-protocol", "twitter":"https://x.com/virtuals_io","symbol":"VIRTUAL"},
    #            {"full_token_name":"JUPITER", "twitter":"https://x.com/JupiterExchange","symbol":"JUP"},
    #            {"full_token_name":"hyperliquid", "twitter":"https://twitter.com/HyperliquidX","symbol":"HYPE"}]
    # with open("data.txt", "w") as f:
    #     for token in symbols:
    #         f.write(f"\n \nDATA ABOUT: {token.get('symbol')}, FULL TOKEN NAME: {token.get('full_token_name')}, TWITTER: {token.get('twitter')}.\n")
    #         for section, data in prompts.prompts.items():
    #             f.write(f"\n{data.get('title')}\n")
    #             perplexity_result = driver.chat_without_streaming(
    #                 message=data.get("msg") % (token.get('symbol'), token.get('full_token_name'), token.get('twitter'), datetime.now() - timedelta(days=7), datetime.now()),
    #                 prompt=data.get("perplexity_prompt") % (token.get("symbol"), datetime.now() - timedelta(days=7), datetime.now())
    #             )
    #             f.write(perplexity_result)
