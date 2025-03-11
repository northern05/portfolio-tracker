from typing import Annotated
from fastapi import Path, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import dependencies as auth_dependencies
from app.core.errors import errors
from app.core.models import db_helper, User
from . import crud
from .schemas import PortfolioResponse, PortfolioCreate, SimilarAssetsResponse, PortfolioResponseExtended, \
    ConnectTelegram
from app.core.modules_factory import cmc_driver, perplexity_driver, elfa_driver, coin_gecko_driver
from utils.general import create_crypto_sentiment_chart


async def create_portfolio(
        portfolio_data: PortfolioCreate,
        session: AsyncSession = Depends(db_helper.scoped_session_dependency),
) -> PortfolioResponse:
    result = await crud.create(session=session, portfolio_data=portfolio_data)
    return PortfolioResponse.from_orm(result)


async def connect_tg(
        users_data: ConnectTelegram,
        session: AsyncSession = Depends(db_helper.scoped_session_dependency)
):
    user = await auth_dependencies.check_wallet(wallet_address=users_data.wallet, session=session)
    user.telegram_id = users_data.telegram_id
    await session.commit()
    return True


async def get_all_portfolio(
        user: User = Depends(auth_dependencies.check_telegram_id),
        session: AsyncSession = Depends(db_helper.scoped_session_dependency),
) -> list[PortfolioResponse]:
    res = await crud.get_users_assets(session=session, user_id=user.id)
    return res


async def get_selected_portfolio(
        symbol: Annotated[str, Path],
        session: AsyncSession = Depends(db_helper.scoped_session_dependency),

) -> PortfolioResponseExtended:
    portfolio = await crud.get_by_symbol(session=session, symbol=symbol)
    if not portfolio:
        await session.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=errors.portfolio_errors.PROJECT_NOT_FOUND
        )
    response_data = PortfolioResponseExtended.from_orm(portfolio)
    response_data.current_price = cmc_driver.get_current_token_price(symbol=portfolio.symbol)
    message = f"Tell me last important news about {portfolio.symbol}"
    response_data.related_news = perplexity_driver.chat_without_streaming(message=message)
    return response_data


async def get_selected_portfolio_chart(
        symbol: Annotated[str, Path],
        session: AsyncSession = Depends(db_helper.scoped_session_dependency)
) -> PortfolioResponseExtended:
    portfolio = await crud.get_by_symbol(session=session, symbol=symbol)
    if not portfolio:
        await session.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=errors.portfolio_errors.PROJECT_NOT_FOUND
        )
    historical_price = coin_gecko_driver.get_historical_prices(symbol=portfolio.symbol)
    sentiment_score = elfa_driver.get_top_posts(symbol=portfolio.symbol)
    response_data = create_crypto_sentiment_chart(historical_prices=historical_price, sentiment_data=sentiment_score)
    return response_data.getvalue()


async def get_similar_assets(
        asset_symbol: str
) -> list[SimilarAssetsResponse]:
    similar_assets = cmc_driver.get_similar_tokens(symbol=asset_symbol)
    return [SimilarAssetsResponse.from_orm(asset) for asset in similar_assets]


async def delete_portfolio(
        telegram_id: int,
        symbol: str,
        session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    result = await crud.delete_users_portfolio(session=session, telegram_id=telegram_id, symbol=symbol)
    return result
