from typing import Annotated
from fastapi import Path, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import dependencies as auth_dependencies
from app.core.errors import errors
from app.core.models import db_helper, User
from . import crud
from .schemas import PortfolioResponse, PortfolioCreate


async def create_portfolio(
        portfolio_data: PortfolioCreate,
        user: User = Depends(auth_dependencies.check_wallet),
        session: AsyncSession = Depends(db_helper.scoped_session_dependency),
) -> PortfolioResponse:
    result = await crud.create(session=session, portfolio_data=portfolio_data, user_id=user.id)
    return PortfolioResponse.from_orm(result)


async def get_all_portfolio(
        user: User = Depends(auth_dependencies.check_wallet),
        session: AsyncSession = Depends(db_helper.scoped_session_dependency),
) -> list:
    res = await crud.get_users_assets(session=session, user_id=user.id)
    return res


async def get_selected_portfolio(
        portfolio_id: Annotated[int, Path],
        user: User = Depends(auth_dependencies.check_wallet),
        session: AsyncSession = Depends(db_helper.scoped_session_dependency),

):
    portfolio = await crud.get_by_id(session=session, portfolio_id=portfolio_id)
    if not portfolio:
        await session.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=errors.projects.PROJECT_NOT_FOUND
        )
    response_data = PortfolioResponse.from_orm(portfolio)
    return response_data
