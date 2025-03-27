import io
from datetime import datetime, timedelta
import json
from typing import Annotated
from fastapi import Path, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import dependencies as auth_dependencies
from app.core.errors import errors
from app.core.models import db_helper
from . import crud
from .schemas import PortfolioResponse, PortfolioCreate, SimilarAssetsResponse, PortfolioResponseExtended, \
    ConnectTelegram, SentimentScore
from app.core.modules_factory import cmc_driver, perplexity_driver, elfa_driver, coin_gecko_driver, redis_db, \
    llama, twitter_scraper
from utils.general import create_crypto_sentiment_chart
from utils import prompts


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
    full_token_name = coin_gecko_driver.get_data_over_coingecko_id(token_id=portfolio.coingecko_id).get("name")
    response_data = await create_report(
        symbol=portfolio.symbol,
        full_token_name=full_token_name,
        data=response_data,
        twitter=portfolio.twitter
    )
    response_data = await generate_full_report(data=response_data)
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
    bullish, fud = llama.get_bullish_fud(symbol=symbol, post_data=sentiment_score)
    response_data = SentimentScore(bullish=bullish, fud=fud)
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
            llama_processing = llama.send_message(message=perplexity_result, prompt=v.get("chatgpt_prompt"))
            setattr(data, k, llama_processing)
    twitts_over_asset = await twitter_scraper.fetch_tweets(protocol_name=twitter.split("/")[-1])
    msg = f"There is data from official {twitter} over {full_token_name} ${symbol} {twitts_over_asset}"
    data.twitter_news = llama.send_message(message=msg, prompt=prompts.twikit_prompt).removesuffix("</s>")
    return data


async def generate_full_report(
        data: PortfolioResponseExtended,
):
    message = f"""There is three blocks with 
                General News & Major Events: {data.related_news}, 
                Price Movements & Market Trends: {data.price_movements}, 
                Investment & Ecosystem Updates: {data.investment_landscape}. 
                Please generate a unified report that combines the following three news sections into a cohesive narrative.
                Make report as concise and informative as possible. One short sentence for every news.
                Include twitter news to report but dont say that this news from official twitter account: {data.twitter_news}
                """
    data.full_report = llama.send_message(message=message, prompt=prompts.final_prompt).removesuffix("</s>")
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
        token_id: str = None,
        session: AsyncSession = Depends(db_helper.scoped_session_dependency)
) -> list[SimilarAssetsResponse] | SimilarAssetsResponse:
    similar_assets = coin_gecko_driver.get_similar_tokens(symbol=asset_symbol)
    result = [SimilarAssetsResponse.from_orm(asset) for asset in similar_assets]
    coingecko_ids = await crud.get_similar_assets(session=session, symbol=asset_symbol)
    for _id in coingecko_ids:
        data = coin_gecko_driver.get_data_over_coingecko_id(token_id=_id)
        result.insert(0, SimilarAssetsResponse.from_orm(data))
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
