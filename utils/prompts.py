prompts = [{"related_news": {
    "perplexity_prompt": "retrieve news about the crypto asset %s focusing on events that occurred between %s and %s."
                         "Ensure the target the event occurrence dates (not the publication dates). "
                         "Include language-agnostic keywords since all languages should be accepted (non-English articles will later be translated to English) [Source links at the end]",
    "chatgpt_prompt": "all this news should be drawn up in the form of a template report and duplicates should be removed template format: For each categorized article, generate a concise summary that includes: - The headline - A brief description of the event (including the event date) - Direct source link(s) Format the final report with the following structure: #### *News* [Headline] (Date) – [Concise summary in 2-3 sentences, combining all news in one paragraph]. [Source links at the end].",
    "msg": """General News & Major Events:
        Find news about %s, %s, %s significant developments, such as partnerships, regulations, technological updates, or security incidents (hacks, exploits).
        Ensure the focus is on event occurrence dates, that occurred between %s and %s.
        Please return only high-quality sources. If any content is behind paywalls, summarize key points.""",
    "title": "News"
},
    "price_movements": {
        "perplexity_prompt": """
            Find news articles about past price movements for %s:
            - within %s and %s date range
            - excluding any predictions or forecasts
            - show me all links when you get information
            - [Source links at the end]""",
        "msg": """Price Movements & Market Trends:
            Identify articles discussing past price movements and volatility for %s, %s, %s that occurred between %s and %s.
            Exclude any predictions or speculative forecasts.
            Please return only high-quality sources. If any content is behind paywalls, summarize key points.""",
        "chatgpt_prompt": "all this (news and prices) should be drawn up in the form of a template report and duplicates should be removed template format: For each categorized article, generate a concise summary that includes: - The headline - A brief description of the event (including the event date) - Direct source link(s) Format the final report with the following structure: #### *Price Moves* [Headline] (Date) – [Concise summary in 2-3 sentences, combining all news in one paragraph]. [Source links at the end].",
        "title": "Price Moves"
    },
    "investment_landscape": {
        "perplexity_prompt": """
            Find news articles about investment landscape and ecosystem updates for %s:
            - within %s and %s date range
            - show me all links when you get information
            - [Source links at the end]""",
        "msg": """Investment & Ecosystem Updates:
            Retrieve news related to market adoption, investor sentiment, and ecosystem developments (e.g., institutional interest, major token listings, DeFi integrations) for %s, %s, %s that occurred between %s and %s.
            Please return only high-quality sources. If any content is behind paywalls, summarize key points.""",
        "chatgpt_prompt": """all this news should be drawn up in the form of a template report and duplicates should be removed. news other than the Investment Landscape should be removed template format: For each categorized article, generate a concise summary that includes: - The headline - A brief description of the event (including the event date) - Direct source link(s) Format the final report with the following structure: #### *Investment Landscape* [Headline] (Date) – [Concise summary in 2-3 sentences, combining all news in one paragraph]. [Source links at the end].""",
        "title": "Investment Landscape"
    }
}]

keywords = f"""
            Language-agnostic keywords for searching related news include:
            - **Cryptocurrency**
            - **Blockchain**
            - **Market Trends**
            - **Whale Activity**
            - **Futures Launch**
            """

final_prompt = """Please generate a unified report that combines the following three news sections into a cohesive narrative. 
Ensure that each section includes the corresponding URL to its original source. 
Format the report with clear headings for each section, and present the information in a concise and informative manner.
Information should not be repeated, if it is repeated, then decide which block it is closer to and leave it only in it. 
Duplicate news was removed, leaving only one
###Output Format###
Price Moves
<content> / up to 2 sentences
Updates (do not include any data about price moves here)
<1. updates> / up to 2 sentences per each news
<2. updates> / up to 2 sentences per each news
<3. updates> / up to 2 sentences per each news
<4. updates> / up to 2 sentences per each news
<5. updates> / up to 2 sentences per each news"""
