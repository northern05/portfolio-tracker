import logging

from sqlalchemy.ext.asyncio import AsyncSession

from .llm_service import answer_users_msg
from .schemas import LlmResponse
from ..core.models.base import ConversationStatus

logger = logging.getLogger('llm')


async def process_user_message(message: str, user_address: str, history_uiid: str,
                               session: AsyncSession, is_shilling_allowed: bool) -> LlmResponse:
    last_response = None
    for _ in range(3):
        flow_result, decision, aux_data = await answer_users_msg(
            msg=message,
            history_uiid=history_uiid,
            session=session,
            is_shilling_allowed=is_shilling_allowed
        )

        logger.info(flow_result)
        last_response = LlmResponse(
            text=flow_result,
            decision=decision.value,
            aux_data=aux_data
        )
        if not is_shilling_allowed:
            return last_response
        if is_shilling_allowed and decision != ConversationStatus.ready_to_shilling and flow_result is not None:
            return last_response
    return last_response

