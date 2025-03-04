from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.models import Portfolio, User, TwitterPost, Token, Trade, ChatActionExtension
from app.core.models.trade import TradeTypeEnum
from ...core.models.agent_balance import AgentBalanceChange
from ...core.models.sharing import Sharing
from ...core.models.trade_position import TradePosition


async def create_users_retwitt(
        user_id: int,
        session: AsyncSession,
        twitter_post_id: str
):
    """
    Method to create chat
    :param session: session to connect to database
    :param user_id: user id created chat
    :return: chat or None if chat not exists
    """
    credit = Portfolio(
        user_id=user_id,
        twitter_post_id=twitter_post_id,
        is_used=False
    )
    session.add(credit)
    await session.commit()
    return credit


async def has_user_available_credits(user_id: int, session: AsyncSession) -> bool:
    """
    Check if the user has available credits with is_used = False.

    :param user_id: ID of the user to check.
    :param session: AsyncSession instance for the database.
    :return: True if credits are available, False otherwise.
    """
    stmt = (
        select(Portfolio)
        .filter(Portfolio.user_id == user_id)
        .filter(Portfolio.is_used == False)
    )
    result = await session.execute(stmt)
    credit = result.scalars().first()
    return credit is not None

async def get_all_twitter_users(session: AsyncSession):
    user_stmt = select(User).filter(User.twitter_id != None)
    result: Result = await session.execute(user_stmt)
    users = result.scalars().all()
    return users


async def get_twitter_posts(session: AsyncSession):
    posts_stmt = select(TwitterPost.twitter_post_id)
    result: Result = await session.execute(posts_stmt)
    posts = result.scalars().all()
    return posts


async def check_existing_retwitted_post(user_id: int, post_id, session: AsyncSession):
    stmt = select(Portfolio).filter(Portfolio.user_id == user_id).filter(Portfolio.twitter_post_id == post_id)
    result: Result = await session.execute(stmt)
    retwitt = result.scalars().all()
    return retwitt


async def get_all_tokens_to_sell(session: AsyncSession):
    """
    Retrieve all Token entities where the amount is greater than zero.
    Returns an empty list if no tokens match the condition.

    :param session: AsyncSession instance.
    :return: List of Token entities with amount > 0.
    """
    stmt = (
        select(
            Trade,
            Token.amount,
            Token.pool_address,
            User
        )
        .join(Token, Token.id == Trade.token_id)
        .join(ChatActionExtension, Trade.chat_uuid == ChatActionExtension.uuid)
        .join(User, ChatActionExtension.user_id == User.id)
        .join(TradePosition, TradePosition.id == Trade.trade_position_id )
        .filter(Token.amount > 0)
        .filter(Trade.created_at <= datetime.now() - timedelta(hours=24))
        .filter(Trade.trade_type == TradeTypeEnum.open.value)
        .filter(TradePosition.is_open == True)
    )

    result = await session.execute(stmt)
    rows = result.fetchall()
    return rows


async def update_user(
        session: AsyncSession,
        wallet: str,
        twitter_id: str,
):
    stmt = (
        select(User)
        .where(User.wallet == wallet)
    )
    result: Result = await session.execute(stmt)
    user: User | None = result.scalars().first()
    user.twitter_id = twitter_id
    await session.commit()
    return user


async def create_sharing(
        session: AsyncSession,
        user_id: int,
        trade_id: int,
        amount: float,
        tx_id: str,
        solana_price: float
) -> Sharing:
    """
    Create a new Sharing record only if the associated Trade is closed.

    Args:
        session: An AsyncSession instance for database operations.
        user_id: The ID of the user creating the sharing.
        trade_id: The ID of the trade associated with this sharing.
        amount: The amount value for the sharing.
        tx_id: The transaction ID for the sharing.

    Returns:
        The newly created Sharing object.

    Raises:
        ValueError: If the trade does not exist or is not closed.
    """
    stmt = select(Trade).where(Trade.id == trade_id)
    result = await session.execute(stmt)
    trade = result.scalars().first()

    if trade is None:
        raise ValueError(f"Trade with id {trade_id} does not exist.")

    if trade.trade_type != TradeTypeEnum.closed:
        raise ValueError("Trade must be closed to create a sharing.")

    sharing = Sharing(user_id=user_id, trade_id=trade_id, amount=amount, tx_id=tx_id, solana_price=solana_price)
    session.add(sharing)

    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        await session.close()
        raise e

    return sharing


async def create_agent_balance_change(
        session: AsyncSession,
        amount: float,
        sol_amount: float
) -> AgentBalanceChange:
    sharing = AgentBalanceChange(amount=amount, sol_amount=sol_amount)
    session.add(sharing)

    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        await session.close()
        raise e

    return sharing
