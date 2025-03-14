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
        self.main_prompt = f"""all this (news and prices) should be drawn up in the form of a template report and duplicates should be removed
            template format:
            For each categorized article, generate a concise summary that includes:
            - The headline
            - A brief description of the event (including the event date)
            - Direct source link(s)
            
            Format the final report with the following structure:
            
            #### **Price Moves**
            1. [Headline] – Brief summary (Date)
               - Source link(s)
            
            #### **Ecosystem Updates, Partnerships & Announcements**
            2. [Headline] – Brief summary (Date)
               - Source link(s)
            
            #### **Investment Landscape**
            3. [Headline] – Brief summary (Date)
               - Source link(s)
            
            Ensure the output follows this structured format and includes all relevant details.
            
            - be very concise and add only 1 sentence to the news and its link!
            - Add the link at the end of the news, not as a separate line
            - Don't summarize report in the end.
            - Add numbers to core paragraphs.
            - Don't use "Based on the search results provided".
            - Don't use clarification on what the news is based on, just a list with active links on sources
            - **Highlight text headings according to telegram's markdown with **<header>** **
        """
        self.analize_prompt = """
        I have collected the top {X} posts from ELFA Driver related to cryptocurrency discussions. Each post includes text content, engagement metrics (likes, comments, shares), and timestamps. Please analyze these posts based on the following criteria:
        Sentiment Analysis: Determine whether each post expresses a positive (bullish), negative (FUD), or neutral sentiment. Provide an overall sentiment breakdown.
        Key Topics & Trends: Identify the main topics discussed (e.g., Bitcoin, Ethereum, regulations, market predictions). Summarize the most mentioned subjects.
        Top Bullish Post: Identify the most engaging bullish post (highest likes/comments/shares) that reflects strong positive sentiment.
        Top FUD/Negative Post: Identify the most engaging FUD/negative post that reflects concerns, fear, or uncertainty.
        Emotional Tone & Language: Analyze the tone (e.g., hype, panic, confidence, uncertainty).
        Market Impact Correlation: If possible, suggest whether sentiment trends align with market movements (e.g., does bullish sentiment coincide with price increases?).
        Anomalies & Noteworthy Insights: Highlight unexpected patterns, viral discussions, or unique viewpoints.
        Return the analysis in a structured format with key takeaways and insights valuable for crypto traders and investors.
        """

    def send_message(self, message: str, temperature: float = 0.7):
        """
        Sends a message to ChatGPT and retrieves the response.

        :param message: String with news from perplexity.
        :param temperature: Controls response randomness (0.0 = deterministic, 1.0 = creative).
        :return: The response text from ChatGPT.
        """
        messages = [
            {
                "role": "system",
                "content": self.main_prompt
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

            return response["choices"][0]["message"]["content"]  # Extract response text

        except Exception as e:
            return f"❌ Error communicating with ChatGPT: {str(e)}"

    def analize_twitter(self, symbol: str, post_data: dict, temperature: float = 0.7):
        """
        Sends a message to ChatGPT and retrieves the response.

        :param message: String with news from perplexity.
        :param temperature: Controls response randomness (0.0 = deterministic, 1.0 = creative).
        :return: The response text from ChatGPT.
        """
        message = f"""
        Parse X posts which i add in posts data with ${symbol.upper()} and retrieve 1 Top Bullish Post (most engaging one) and 1 Top FUD / Negative post.
        Posts data: {post_data}
        **Don't use "Based on your provided data, here is the requested analysis:"**
        **Highlight text headings according to telegram's markdown with **<header>** **
        **Вo not use the description of the analysis method**
        """
        messages = [
            {
                "role": "system",
                "content": self.analize_prompt
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
