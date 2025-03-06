class PortfolioErrors:
    GOOGLE_API_RESOURCE_EXHAUSTED = "Google API quota limits reached"
    PORTFOLIO_NOT_FOUND = "Portfolio not found!"
    ASSET_NOT_FOUND = "Asset not found!"
    USER_NOT_OWNER = "That's not your chat!"

class LLMErrors:
    CALL_FUNCTION_ERROR = "Call function error!"
    TWITTER_POST_ERROR = "Twitter post error!"


class Errors:
    chats = PortfolioErrors()
    llm_errors = LLMErrors()


errors = Errors()