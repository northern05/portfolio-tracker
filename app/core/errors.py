class ChatErrors:
    GOOGLE_API_RESOURCE_EXHAUSTED = "Google API quota limits reached"
    CHAT_NOT_FOUND = "Chat not found!"
    USER_NOT_OWNER = "That's not your chat!"

class LLMErrors:
    CALL_FUNCTION_ERROR = "Call function error!"
    TWITTER_POST_ERROR = "Twitter post error!"


class Errors:
    chats = ChatErrors()
    llm_errors = LLMErrors()


errors = Errors()