prompts = [{"news": {
    "perplexity_prompt": "retrieve news about the crypto asset %s focusing on events that occurred between 08.03.2025 and 16.03.2025. Ensure the target the event occurrence dates (not the publication dates). Include language-agnostic keywords since all languages should be accepted (non-English articles will later be translated to English)",
    "chatgpt_prompt": "",
    "title": ""
},
    "price_movements": {
        "perplexity_prompt": """
        Find news articles about past price movements:
        - within 08.03.2025 and 16.03.2025 date range
        - excluding any predictions or forecasts
        - show me all links when you get information""",
        "chatgpt_prompt": "",
        "title": ""
    },
    "investment landscape": {
        "perplexity_prompt": """
        Find news articles about investment landscape and ecosystem updates:
        - within 08.03.2025 and 16.03.2025 date range
        - show me all links when you get information""",
        "chatgpt_prompt": "",
        "title": ""
    }
}]
