import logging
from typing import Optional

from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth.dependencies import check_wallet
from app.api.portfolio import crud
from app.api.portfolio.crud import get_sum_of_paid_messages, get_max_min_pnl_sql, get_agent_transactions, \
    get_agent_rejections, get_agent_balance_in_sol, get_agent_balance_summary, get_count_of_approved_tokens, \
    get_dashboard_stats, get_assets_summary, get_user_transactions, get_trades_summary_general
from app.api.portfolio.schemas import MessageCountResponse, UsersCountResponse, ShillingStatisticsAction, \
    ShillingStatisticsResponse
from app.core.models import db_helper, User
from app.core.models.base import ActionParameter

router = APIRouter(tags=["Statistics"])

logger = logging.getLogger('portfolio/views')


# @router.get(
#     "/messages",
#     status_code=status.HTTP_200_OK,
#     response_model=MessageCountResponse,
# )
# async def get_all_messages_count(
#         session: AsyncSession = Depends(db_helper.scoped_session_dependency),
# ):
#     """
#     Endpoint to get portfolio over user messages
#     :param session: session to connect to database
#     :return: messages portfolio
#     """
#     logger.info("Received get messages count request")
#
#     count = await crud.get_message_count(
#         session=session,
#     )
#     return MessageCountResponse(total_messages=count)



@router.get(
    "/messages",
    status_code=status.HTTP_200_OK,
    response_model=MessageCountResponse,
)
async def get_messages_count_by_user_action(
        action_param: ActionParameter,
        user: User = Depends(check_wallet),
        session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    """
    Endpoint to get portfolio over user messages based on action
    :param session: session to connect to database
    :param user: user address
    :param action_param: action parameter
    :return: messages portfolio
    """
    logger.info("Received get messages count request")

    count = await crud.get_message_count_by_user_address_action(
        action_param=action_param,
        user=user,
        session=session,
    )
    return MessageCountResponse(total_messages=count)

@router.get(
    "/users",
    status_code=status.HTTP_200_OK,
    response_model=UsersCountResponse,
)
async def get_all_users_count(
        session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    """
    Endpoint to get portfolio over users
    :param session: session to connect to database
    :return: users portfolio
    """
    logger.info("Received get users count request")

    count = await crud.get_unique_users_count(
        session=session,
    )
    return UsersCountResponse(total_users=count)


@router.get(
    "/shilling",
    status_code=status.HTTP_200_OK,
    response_model=ShillingStatisticsResponse,
)
async def get_shilling_statistics(
        action_param: ShillingStatisticsAction,
        user_address: Optional[str] = None,
        session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    """
    Endpoint to get portfolio over user's trade
    :action_param: parameter of action to be executed
    :param session: session to connect to database
    :return: users portfolio
    """
    logger.info(f"Received portfolio request with action: {action_param.value}")

    if action_param == ShillingStatisticsAction.dashboard_info:
        result = await get_dashboard_stats(session)
    elif action_param == ShillingStatisticsAction.total_paid:
        output = await get_sum_of_paid_messages(session)
        result = {'sum': f'{output:.9f}'}
    elif action_param == ShillingStatisticsAction.max_min_trade_pnl:
        max_pnl, min_pnl, max_tx_id, max_symbol, min_tx_id, min_symbol = await get_max_min_pnl_sql(session)
        result = {
            "max": {
                "pnl": f'{max_pnl:.9f}',
                "tx_id": max_tx_id,
                "symbol": max_symbol
            },
            "min": {
                "pnl": f'{min_pnl:.9f}',
                "tx_id": min_tx_id,
                "symbol": min_symbol
            }
        }
    elif action_param == ShillingStatisticsAction.transactions:
        if user_address:
            result = await get_user_transactions(session=session, user_address=user_address)
        else:
            result = await get_agent_transactions(session=session)
    elif action_param == ShillingStatisticsAction.rejections:
        result = await get_agent_rejections(session=session)
    elif action_param == ShillingStatisticsAction.current_balance:
        result = get_agent_balance_in_sol()
    elif action_param == ShillingStatisticsAction.trades:
        result = await get_trades_summary_general(session=session)
    elif action_param == ShillingStatisticsAction.agent_balance_by_minutes:
        result = await get_agent_balance_summary(session=session, period='5min')
    elif action_param == ShillingStatisticsAction.agent_balance_by_day:
        result = await get_agent_balance_summary(session=session, period='hour')
    elif action_param == ShillingStatisticsAction.agent_balance_by_week:
        result = await get_agent_balance_summary(session=session, period='week')
    elif action_param == ShillingStatisticsAction.agent_balance_by_month:
        result = await get_agent_balance_summary(session=session, period='month')
    elif action_param == ShillingStatisticsAction.agent_balance_by_year:
        result = await get_agent_balance_summary(session=session, period='year')
    elif action_param == ShillingStatisticsAction.tokens_approved:
        output = await get_count_of_approved_tokens(session=session)
        result = {'count': output}
    elif action_param == ShillingStatisticsAction.assets:
        result = await get_assets_summary(session=session)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown parameter: {action_param}")
    return ShillingStatisticsResponse(result=result)