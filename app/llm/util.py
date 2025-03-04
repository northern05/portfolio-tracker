import uuid

from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from app.core.models.base import ConversationStatus
from app.core.modules_factory import LLM_OPEN_AI


async def get_reply(messages, tools, config: dict = None):
    """
    Helper that calls the chat_completion API with the given messages and tools,
    verifies that a reply is returned, and returns it.
    """
    graph = create_react_agent(LLM_OPEN_AI, tools=tools, checkpointer=MemorySaver())
    input = {"messages": messages}
    conversation_status = ConversationStatus.discuss
    info = None
    last_response = ""

    default_configurable = {"thread_id": uuid.uuid4()}
    configurable = {**default_configurable, **(config if config else {})}

    async for step in graph.astream(input=input, config={"configurable": configurable}, stream_mode='values'):
        last_response = step['messages'][-1]
        if hasattr(last_response, "name") and last_response.name:
            name = last_response.name
            if name == 'identifyPool':
                info = last_response.artifact
                if info is not None:
                    conversation_status = ConversationStatus.ready_to_shilling
            elif name == 'rejectShilling':
                conversation_status = ConversationStatus.reject
            elif name == 'approveShilling':
                info = last_response.artifact
                if info is not None:
                    conversation_status = ConversationStatus.approve

    return last_response.content, conversation_status, info
