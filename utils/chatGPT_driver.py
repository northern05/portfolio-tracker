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
            1. [Headline] – Brief summary (Date)
               - Source link(s)
            
            #### **Investment Landscape**
            1. [Headline] – Brief summary (Date)
               - Source link(s)
            
            Ensure the output follows this structured format and includes all relevant details.
            
            - be very concise and add only 1 sentence to the news and its link!
            - Add the link at the end of the news, not as a separate line
        """

    async def send_message(self, message: str, temperature: float = 0.7):
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
            response = await openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                temperature=temperature
            )

            return response["choices"][0]["message"]["content"]  # Extract response text

        except Exception as e:
            return f"❌ Error communicating with ChatGPT: {str(e)}"

    def format_message(self, role: str, content: str):
        """
        Formats a message into OpenAI's expected structure.

        :param role: The role of the message sender ("system", "user", or "assistant").
        :param content: The message content.
        :return: A properly formatted message dictionary.
        """
        return {"role": role, "content": content}
