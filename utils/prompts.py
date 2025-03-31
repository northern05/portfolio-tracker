prompts = [{"related_news": {
    "perplexity_prompt": "retrieve news about the crypto asset %s focusing on events that occurred between %s and %s."
                         "Ensure the target the event occurrence dates (not the publication dates). "
                         "Include language-agnostic keywords since all languages should be accepted (non-English articles will later be translated to English) [Source links at the end]",
    "chatgpt_prompt": "all this news should be drawn up in the form of a template report and duplicates should be removed template format: "
                      "For each categorized article, generate a concise summary that includes: "
                      "- The headline - A brief description of the event (including the event date) "
                      "- Direct source link(s) Format the final report with the following structure: "
                      "#### Updates [Headline] (Date) – [Concise summary in 2-3 sentences, combining all news in one paragraph]. "
                      "[Active source links at the end]. Maximum 500 symbols.",
    "msg": """General News & Major Events:
        Find news about %s, %s, %s significant developments, such as partnerships, regulations, technological updates, or security incidents (hacks, exploits).
        Ensure the focus is on event occurrence dates, that occurred between %s and %s.
        Please return only high-quality sources. If any content is behind paywalls, summarize key points.
        [Active source links at the end].""",
    "title": "News",
    "check": "Is there any recent news about %s? Please answer with 'yes' or 'no' only."
},
    "price_movements": {
        "perplexity_prompt": """
            Retrieve news articles detailing actual price movements of %s strictly within %s and %s date range. Exclud any predictions or forecasts
            - show me all links when you get information
            - [Active source source links at the end]""",
        "msg": """Price Movements & Market Trends:
            Identify articles discussing past price movements and volatility for %s, %s, %s that occurred between %s and %s.
            Exclude any predictions or speculative forecasts.
            Please return only high-quality sources. If any content is behind paywalls, summarize key points.
            [Active source links at the end].""",
        "chatgpt_prompt": "all this (news and prices) should be drawn up in the form of a template report and duplicates "
                          "should be removed template format: For each categorized article, generate a concise summary that includes: "
                          "- The headline - A brief description of the event (including the event date) "
                          "- Direct source link(s) Format the final report with the following structure: "
                          "#### Price Moves [Headline] (Date) – [Concise summary in 2-3 sentences, combining all news in one paragraph]. "
                          "[Active source links at the end]. Maximum 200 symbols.",
        "title": "Price Moves",
        "check": "Find some news about price movements about $%s?"
    },
    # "investment_landscape": {
    #     "perplexity_prompt": """
    #         Find news articles about investment landscape and ecosystem updates for %s:
    #         - within %s and %s date range
    #         - show me all links when you get information
    #         - [Source links at the end]""",
    #     "msg": """Investment & Ecosystem Updates:
    #         Retrieve news related to market adoption, investor sentiment, and ecosystem developments (e.g., institutional interest, major token listings, DeFi integrations) for %s, %s, %s that occurred between %s and %s.
    #         Please return only high-quality sources. If any content is behind paywalls, summarize key points.
    #         [Source links at the end].""",
    #     "chatgpt_prompt": """all this news should be drawn up in the form of a template report and duplicates should be removed. news other than the Investment Landscape should be removed template format: For each categorized article, generate a concise summary that includes: - The headline - A brief description of the event (including the event date) - Direct source link(s) Format the final report with the following structure: #### *Investment Landscape* [Headline] (Date) – [Concise summary in 2-3 sentences, combining all news in one paragraph]. [Source links at the end]. Maximum 1000 symbols.""",
    #     "title": "Investment Landscape",
    #     "check": "Is there any recent investment landscape about %s? Please answer with 'yes' or 'no' only."
    # }
}]

keywords = f"""
            Language-agnostic keywords for searching related news include:
            - **Cryptocurrency**
            - **Blockchain**
            - **Market Trends**
            - **Whale Activity**
            - **Futures Launch**
            """

final_prompt = """Generate a final report that combines the two sections into a cohesive narrative. 
Squeeze all message maximum to 1000 symbols in message.
If No updates - write "No updates"
###Output Format###
#### Price Moves
<content> / up to 1 short sentence maximum 200 symbols.
#### Updates (do not include any data about price moves here, only Investment & Ecosystem Updates and General News & Major Events)
<1. updates> / up to 1 short sentences per each news maximum 200 symbols.
<2. updates> / up to 1 short sentences per each news maximum 200 symbols.
<3. updates> / up to 1 short sentences per each news maximum 200 symbols.
Save all sources and links in the end of the message
MAXIMUM 1000 symbols without links.
[Active source links at the end].
ADD all active links in the end
"""

twikit_prompt = """
Analyze the following Twitter posts from the official cryptocurrency account and extract news, key insights, trends, and patterns. 
Identify mentions of cryptocurrency price updates, engagement levels (likes/retweets), and sentiment shifts. 
Highlight any significant events or announcements. Also, summarize how the cryptocurrency community is reacting based on engagement metrics.
Answer in one short sentence.
"""

bullish_fud_prompts = {
    "bullish": "You are sentiment analyzing agent. Return TOP 1 bullish post based on posts data provided in JSON format for specified Token ticker. Use engagement metrics to pick the post from the most Bullish ones. Use output format for response: {'twitter_user_id': <twitter_user_id>, 'twitter_id': <twitter_id>} \n###########################################",
    "fud": "You are sentiment analyzing agent. Return TOP 1 Bearish/FUD post based on posts data provided in JSON format for specified Token ticker. Use engagement metrics to pick the post from the most Bearish/FUD ones. Use output format for response: {'twitter_user_id': <twitter_user_id>, 'twitter_id': <twitter_id>} \n###########################################"
}
