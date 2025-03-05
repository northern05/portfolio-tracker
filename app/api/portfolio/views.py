import logging
from typing import Optional

from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth.dependencies import check_wallet
from . import crud, dependencies, schemas
from app.core.models import db_helper, User
from app.core.models.base import ActionParameter

router = APIRouter(tags=["Portfolio"])

logger = logging.getLogger('portfolio/views')


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=list[schemas.PortfolioResponse],
)
async def get_all_messages_count(
        result: list[schemas.PortfolioResponse] = Depends(dependencies.get_all_portfolio)
):
    """
    Endpoint to get portfolio over user
    :param session: session to connect to database
    :return: list portfolio
    """
    return result



@router.get(
    "/{portfolio_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.PortfolioResponseExtended,
)
async def get_selected_portfolio(
        result: schemas.PortfolioResponseExtended = Depends(dependencies.get_selected_portfolio)
):
    """
    Endpoint to get selected portfolio over user
    :param user: user address
    :return: portfolio extended schema
    """
    return result

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
