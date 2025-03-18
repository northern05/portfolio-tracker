import io
from datetime import datetime, timedelta
import json
from typing import Annotated
from fastapi import Path, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import dependencies as auth_dependencies
from app.core.errors import errors
from app.core.models import db_helper, User
from . import crud
from .schemas import PortfolioResponse, PortfolioCreate, SimilarAssetsResponse, PortfolioResponseExtended, \
    ConnectTelegram, SentimentScore
from app.core.modules_factory import cmc_driver, perplexity_driver, elfa_driver, coin_gecko_driver, chatgpt
from utils.general import create_crypto_sentiment_chart
from utils import prompts
from app.core.modules_factory import redis_db


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
        telegram_id: Annotated[str, Path],
        session: AsyncSession = Depends(db_helper.scoped_session_dependency),
) -> list[PortfolioResponse]:
    res = await crud.get_users_assets(session=session, telegram_id=telegram_id)
    return res


async def get_selected_portfolio(
        symbol: Annotated[str, Path],
        session: AsyncSession = Depends(db_helper.scoped_session_dependency),

) -> PortfolioResponseExtended:
    portfolio = await crud.get_by_symbol(session=session, symbol=symbol)
    cash_data = await redis_db.get(portfolio.symbol)
    if cash_data:
        return PortfolioResponseExtended.parse_obj(json.loads(cash_data.decode("UTF-8")))
    if not portfolio:
        await session.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=errors.portfolio_errors.PROJECT_NOT_FOUND
        )
    response_data = PortfolioResponseExtended.from_orm(portfolio)
    response_data.current_price = cmc_driver.get_current_token_price(symbol=portfolio.symbol)
    full_token_name = coin_gecko_driver.get_token_name(symbol=portfolio.symbol, token_id=portfolio.coingecko_id)
    response_data = await create_report(
        symbol=portfolio.symbol,
        full_token_name=full_token_name,
        data=response_data,
        twitter=portfolio.twitter
    )
    await redis_db.set(portfolio.symbol, response_data.json(), ex=86400)
    return response_data


async def get_sentiment_score(
        symbol: Annotated[str, Path],
        session: AsyncSession = Depends(db_helper.scoped_session_dependency),

) -> SentimentScore:
    portfolio = await crud.get_by_symbol(session=session, symbol=symbol)
    cash_data = await redis_db.get(f"{portfolio.symbol}_sentiment")
    if cash_data:
        return SentimentScore.parse_obj(json.loads(cash_data.decode("UTF-8")))
    if not portfolio:
        await session.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=errors.portfolio_errors.PROJECT_NOT_FOUND
        )
    sentiment_score = elfa_driver.get_squeeze(symbol=portfolio.symbol)
    response_data = SentimentScore(
        sentiment_score=chatgpt.post_llama(symbol=symbol, post_data=sentiment_score).removesuffix("</s>").replace('\n', '  \n'))
    await redis_db.set(f"{portfolio.symbol}_sentiment", response_data.json(), ex=86400)
    return response_data


async def create_report(
        symbol: str,
        full_token_name: str,
        data: PortfolioResponseExtended,
        twitter: str = None
):
    for block in prompts.prompts:
        for k, v in block.items():
            perplexity_result = perplexity_driver.chat_without_streaming(
                message=v.get("msg") % (
                    symbol, full_token_name, twitter, datetime.now() - timedelta(days=7), datetime.now()),
                prompt=v.get("perplexity_prompt") % (symbol, datetime.now() - timedelta(days=7), datetime.now())
            )
            chatgpt_processing = chatgpt.send_message(message=perplexity_result, prompt=v.get("chatgpt_prompt"))
            setattr(data, k, chatgpt_processing)
    return data


async def get_selected_portfolio_chart(
        symbol: Annotated[str, Path],
        session: AsyncSession = Depends(db_helper.scoped_session_dependency)
) -> bytes:
    portfolio = await crud.get_by_symbol(session=session, symbol=symbol)
    cash_data = await redis_db.get(f"{portfolio.symbol}_graph")
    if cash_data:
        return cash_data
    if not portfolio:
        await session.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=errors.portfolio_errors.PROJECT_NOT_FOUND
        )
    historical_price = coin_gecko_driver.get_historical_prices(symbol=portfolio.symbol)
    # sentiment_score = elfa_driver.get_top_posts(symbol=portfolio.symbol)
    response_data = create_crypto_sentiment_chart(historical_prices=historical_price)
    await redis_db.set(f"{portfolio.symbol}_graph", response_data.getvalue(), ex=86400)
    return response_data.getvalue()


async def get_similar_assets(
        asset_symbol: str,
        token_id: str = None
) -> list[SimilarAssetsResponse]:
    similar_assets = coin_gecko_driver.get_similar_tokens(symbol=asset_symbol)
    result = [SimilarAssetsResponse.from_orm(asset) for asset in similar_assets]
    if token_id:
        token = list(filter(lambda x: token_id == x.token_id, result))
        result = SimilarAssetsResponse.from_orm(token[0])
        result.twitter = coin_gecko_driver.get_twitter_from_coingecko(token_id=result.token_id)
    return result


async def delete_portfolio(
        telegram_id: str,
        symbol: str,
        session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    result = await crud.delete_users_portfolio(session=session, telegram_id=telegram_id, symbol=symbol)
    return result
