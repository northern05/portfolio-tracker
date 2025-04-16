final_price_movements_prompt = """Generate a final for specified Token ticker report based on provided data from users message
###Output Format###
#### Price Moves
\n <content> / up to 1 short sentence.
###Maximum 150 symbols.
Do not add data that is not related to price movements here.
"""

final_updates_prompt = """Generate a final report for specified Token ticker based on provided data from users message.
If No updates - write "No updates"
###Output Format###
#### Updates (do not include any data about price moves here, only investment, ecosystem updates, general news and major events)
\n <1. updates> / up to 1 short sentences per each news maximum 200 symbols.
\n <2. updates> / up to 1 short sentences per each news maximum 200 symbols.
\n <3. updates> / up to 1 short sentences per each news maximum 200 symbols.
MAXIMUM 600 symbols without links.
#Active source links at the end.
"""

prompts = {"price_movements": {
    "perplexity_prompt": """
            Retrieve news articles detailing actual price movements of %s strictly within %s and %s date range. Exclude any predictions or forecasts""",
    "msg": """Price Movements & Market Trends:
            Identify articles discussing past price movements and volatility for %s, %s, %s that occurred between %s and %s.
            Exclude any predictions or speculative forecasts.
            Please return only high-quality sources. If any content is behind paywalls, summarize key points.""",
    # "chatgpt_prompt": "all this (news and prices) should be drawn up in the form of a template report and duplicates "
    #                   "should be removed template format: For each categorized article, generate a concise summary that includes: "
    #                   "- The headline - A brief description of the event (including the event date) "
    #                   "- Direct source link(s) Format the final report with the following structure: "
    #                   "#### Price Moves [Headline] (Date) – [Concise summary in 2-3 sentences, combining all news in one paragraph]. "
    #                   "[Active source links at the end]. Maximum 200 symbols.",
    "chatgpt_prompt": final_price_movements_prompt,
    "title": "Price Moves",
    "check": "Find some news about price movements about $%s?"
},
    # "related_news": {
    #     "perplexity_prompt": "retrieve news about the crypto asset %s focusing on events that occurred between %s and %s."
    #                          "Ensure the target the event occurrence dates (not the publication dates). "
    #                          "Include language-agnostic keywords since all languages should be accepted (non-English articles will later be translated to English) [Source links at the end]",
    #     # "chatgpt_prompt": "all this news should be drawn up in the form of a template report and duplicates should be removed template format: "
    #     #                   "For each categorized article, generate a concise summary that includes: "
    #     #                   "- The headline - A brief description of the event (including the event date) "
    #     #                   "- Direct source link(s) Format the final report with the following structure: "
    #     #                   "#### Updates [Headline] (Date) – [Concise summary in 2-3 sentences, combining all news in one paragraph]. "
    #     #                   "[Active source links at the end]. Maximum 500 symbols.",
    #     "chatgpt_prompt": final_updates_prompt,
    #     "msg": """Updates:
    #     Find news about %s, %s, %s significant developments, such as partnerships, regulations, technological updates, or security incidents (hacks, exploits).
    #     Ensure the focus is on event occurrence dates, that occurred between %s and %s.
    #     Please return only high-quality sources. If any content is behind paywalls, summarize key points.
    #     [Active source links at the end].""",
    #     "title": "Updates",
    #     "check": "Is there any recent news about %s? Please answer with 'yes' or 'no' only."
    # },
}

twikit_prompt = """
Analyze the following Twitter posts from the official cryptocurrency account and extract news, key insights, trends, and patterns. 
Identify mentions of cryptocurrency price updates, engagement levels (likes/retweets), and sentiment shifts. 
Highlight any significant events or announcements. Drop duplicates.
If No updates - write "No updates"
###Output Format###
#### Updates 
\n <1. updates> / up to 1 short sentence.
\n <2. updates> / up to 1 short sentence.
\n <3. updates> / up to 1 short sentence.
#MAXIMUM 300 symbols without links.
#DO NOT add Engagement levels or Sentiment
"""

twikit_prompt_solo = """
Analyze the following Twitter posts from the official cryptocurrency account and extract news, key insights, trends, and patterns. 
Identify mentions of cryptocurrency price updates, engagement levels (likes/retweets), and sentiment shifts. 
Highlight any significant events or announcements.
###Output Format: 1 short sentence maximum 100 symbols.
"""

bullish_fud_score_prompt = "Process data, score twitter post from 1 to 100, where score 1 is TOP 1 Bearish/FUD, and score 100 is TOP 1 Bullish post based on post data provided for specified %s. Use engagement metrics to rate the post. #Answer only number."

top_1_bullish = "Process data, and choose TOP 1 Bullish post based on post data provided for specified %s. #Return chosen post in JSON format."
top_1_fud = "Process data, and choose TOP 1 Bearish/FUD post based on post data provided for specified %s. #Return chosen post in JSON format."