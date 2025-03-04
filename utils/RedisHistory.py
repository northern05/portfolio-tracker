from typing import Optional, Any

import jsonpickle
from langchain_core.messages import SystemMessage, HumanMessage
from redis import Redis, ResponseError


class RedisChatMessageHistory:
    def __init__(
            self,
            uiid_session: str,
            redis_url: str = "redis://localhost:6379",
            redis_client: Optional[Redis] = None,
            **kwargs: Any,
    ):
        self.redis_client = redis_client or Redis.from_url(redis_url, **kwargs)
        try:
            self.redis_client.client_setinfo("LIB-NAME", 'v1')
        except ResponseError:
            # Fall back to a simple log echo
            self.redis_client.echo('v1')
        self.uiid_session = uiid_session

    def base_messages(self):
        results = self.redis_client.get(self.uiid_session)
        if not results:
            return []
        decoded_messages = jsonpickle.decode(results)
        return [
            SystemMessage(content=msg['content']) if msg['role'] == 'system'
            else HumanMessage(content=msg['content'])
            for msg in decoded_messages
        ] if decoded_messages else []

    async def add_message(self, role, content):
        """
        Adds a new message to the history and saves it back to Redis.
        """
        existing_messages = self.base_messages()
        existing_messages.append({'role': role, 'content': content})
        self.redis_client.set(self.uiid_session, jsonpickle.encode(existing_messages))
