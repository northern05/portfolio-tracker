from sqlalchemy import select
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import PortfolioCreate, PortfolioUpdate, PortfolioResponse
from app.core.models import Portfolio, PortfolioUser


async def get_users_assets(session: AsyncSession, user_id: int) -> list | None:
    stmt = (
        select(Portfolio)
        .join(PortfolioUser, PortfolioUser.portfolio_id == Portfolio.id)
        .filter(PortfolioUser.user_id == user_id)
        .order_by(Portfolio.symbol)
    )
    result: Result = await session.execute(stmt)
    users_portfolio = result.scalars().all()
    return [PortfolioResponse.from_orm(portfolio) for portfolio in users_portfolio]


async def create(session: AsyncSession, portfolio_data: PortfolioCreate, user_id: int) -> Portfolio | None:
    portfolio = await get_by_symbol(session=session, symbol=portfolio_data.symbol)
    if not portfolio:
        portfolio = Portfolio(
            **portfolio_data.model_dump(),
        )
        session.add(portfolio)
        await session.commit()
    portfolio_user = PortfolioUser(portfolio_id=portfolio.id, user_id=user_id)
    session.add(portfolio_user)
    await session.commit()
    return portfolio


async def get_by_id(session: AsyncSession, portfolio_id: int) -> Portfolio | None:
    stmt = (
        select(Portfolio)
        .filter(Portfolio.id == portfolio_id)
    )
    result: Result = await session.execute(stmt)
    portfolio = result.scalars().first()
    return portfolio

async def get_by_symbol(session: AsyncSession, symbol: str) -> Portfolio | None:
    stmt = (
        select(Portfolio)
        .filter(Portfolio.symbol == symbol)
    )
    result: Result = await session.execute(stmt)
    portfolio = result.scalars().first()
    return portfolio


async def update_portfolio(
        session: AsyncSession,
        portfolio: Portfolio,
        portfolio_update: PortfolioUpdate,
        partial: bool = False,
) -> Portfolio:
    for name, value in portfolio_update.model_dump(exclude_unset=partial).items():
        setattr(portfolio, name, value)
    await session.commit()
    return portfolio


async def delete_project(
        session: AsyncSession,
        portfolio: Portfolio,
) -> None:
    await session.delete(portfolio)
    await session.commit()
