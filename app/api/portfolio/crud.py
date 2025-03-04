import calendar
import datetime
import json
from collections import defaultdict

import pytz
from fastapi import Depends
from sqlalchemy import select, func, text, case
from sqlalchemy.ext.asyncio import AsyncSession

from app import db_helper
from app.api.chats import crud
from app.api.chats.schemas import ExtendedChatExtensionActionSchema
from app.api.portfolio.constants import SOL_IMAGE_URL
from app.core.models import User, ChatActionExtension, Token
from app.core.models.agent_balance import AgentBalanceChange
from app.core.models.base import ActionParameter
from app.core.models.payment import Payment, PaymentTypeEnum, DecisionTypeEnum
from app.core.models.sharing import Sharing
from app.core.models.trade import Trade, TradeTypeEnum
from app.core.models.trade_position import TradePosition
from app.core.modules_factory import redis_db, solana_driver


async def get_unique_users_count(
        session: AsyncSession,
) -> int:
    """
    Method to get unique users count
    :param session: session to connect to database
    :return: unique users count
    """
    stmt = select(func.count(User.id))
    result = await session.execute(stmt)
    user_count = result.scalar()
    return user_count


async def get_message_count_by_user_address_action(
        action_param: ActionParameter,
        user: User,
        session: AsyncSession = Depends(db_helper.scoped_session_dependency),
) -> int:
    chat = await crud.get_chat_by_user_id(session=session, user_id=user.id, action=action_param)

    if not chat:
        chat = await crud.create(user_id=user.id, session=session, action=action_param)

    chat = ExtendedChatExtensionActionSchema.from_orm(chat)
    history = await redis_db.get(chat.uuid)

    if history:
        all_history = json.loads(history)
        filtered_history = []
        for message in all_history:
            if message.get('role') == 'user':
                filtered_history.append(message)
    else:
        filtered_history = []

    return len(filtered_history)


async def count_shilling_messages(session: AsyncSession) -> int:
    """
    Count all ChatActionExtension messages with the action 'shilling'.

    Args:
        session: An instance of AsyncSession for executing database queries.

    Returns:
        The count of messages where action is 'shilling'.
    """
    stmt = select(func.sum(ChatActionExtension.user_message_count)).where(
        ChatActionExtension.action == ActionParameter.shilling)
    result = await session.execute(stmt)
    count = result.scalar_one()
    return count


async def get_all_payments_count_solana(
        session: AsyncSession = Depends(db_helper.scoped_session_dependency),
) -> int:
    """
    Retrieve the count of Payment entities with payment_type set to "solana".

    :param session: AsyncSession instance to connect to the database.
    :return: Count of payments with payment_type "solana".
    """
    stmt = (
        select(func.count(Payment.id))
        .filter(Payment.payment_type == PaymentTypeEnum.solana)
    )

    result = await session.execute(stmt)
    total_payment_count = result.scalar() or 0
    return total_payment_count


async def get_sum_of_paid_messages(
        session: AsyncSession = Depends(db_helper.scoped_session_dependency),
) -> float:
    messages_count = await get_all_payments_count_solana(session)
    return messages_count * 0.0001


async def get_count_of_closed_trades(
        session: AsyncSession = Depends(db_helper.scoped_session_dependency),
) -> int:
    """
    Method to get count of closed trades
    :param session: session to connect to database
    :return: count of closed trades
    """
    stmt = select(func.count(Trade.id)).filter(Trade.trade_type == TradeTypeEnum.closed)
    result = await session.execute(stmt)
    closed_trades_count = result.scalar()
    return closed_trades_count


async def get_count_of_approved_tokens(
        session: AsyncSession = Depends(db_helper.scoped_session_dependency),
) -> int:
    """
    Method to get count of approved tokens.

    Args:
        session: Session to connect to the database.

    Returns:
        Count of approved tokens.
    """
    stmt = select(func.count(Payment.id)).filter(Payment.decision_type == DecisionTypeEnum.approve)
    result = await session.execute(stmt)
    approved_tokens_count = result.scalar() or 0
    return approved_tokens_count


async def get_count_of_trades(
        session: AsyncSession = Depends(db_helper.scoped_session_dependency),
) -> int:
    stmt = select(func.count(Trade.id))
    result = await session.execute(stmt)
    trades_count = result.scalar()
    return trades_count


async def get_sum_of_shared_pnl(
        session: AsyncSession = Depends(db_helper.scoped_session_dependency),
) -> int:
    stmt = select(func.sum(Sharing.amount))
    result = await session.execute(stmt)
    closed_trades_count = result.scalar()
    return closed_trades_count


async def get_average_pnl_sql(session: AsyncSession = Depends(db_helper.scoped_session_dependency), ) -> float:
    """
    Method to calculate the average profit and loss (PnL) using SQL query
    :param session: session to connect to database
    :return: average PnL for matching pairs of trades
    """
    sql = """
             SELECT AVG(closed."baseTokenQuantity" - open."baseTokenQuantity") AS average_pnl
             FROM trades AS open
             JOIN trades AS closed
               ON open.trade_position_id = closed.trade_position_id
             WHERE open.trade_type = 'open'
               AND closed.trade_type = 'closed';
           """

    result = await session.execute(text(sql))
    avg_pnl = result.scalar()

    return avg_pnl if avg_pnl is not None else 0.0


async def get_max_min_pnl_sql(session: AsyncSession) -> tuple:
    """
    Calculate the maximum and minimum profit and loss (PnL) from paired open/closed trades,
    along with the corresponding transaction IDs and token symbols.

    The query computes PnL as (closed.baseTokenQuantity - open.baseTokenQuantity) for each pair
    of open and closed trades (joined via the same chat_uuid), and then returns the maximum and minimum
    values along with the tx_id and token symbol from the closed trade.

    :param session: AsyncSession instance.
    :return: A tuple containing:
             (max_pnl, min_pnl, max_tx_id, max_token_symbol, min_tx_id, min_token_symbol)
    """
    sql = """
        WITH pnl_calc AS (
            SELECT
                (closed."baseTokenQuantity" - open."baseTokenQuantity") AS pnl,
                closed.tx_id,
                t.symbol
            FROM trades open
            JOIN trades closed
                ON open.trade_position_id = closed.trade_position_id
            JOIN tokens t
                ON closed.token_id = t.id
            WHERE open.trade_type = 'open'
              AND closed.trade_type = 'closed'
        )
        SELECT 
            (SELECT pnl FROM pnl_calc ORDER BY pnl DESC LIMIT 1) AS max_pnl,
            (SELECT tx_id FROM pnl_calc ORDER BY pnl DESC LIMIT 1) AS max_tx_id,
            (SELECT symbol FROM pnl_calc ORDER BY pnl DESC LIMIT 1) AS max_symbol,
            (SELECT pnl FROM pnl_calc ORDER BY pnl ASC LIMIT 1) AS min_pnl,
            (SELECT tx_id FROM pnl_calc ORDER BY pnl ASC LIMIT 1) AS min_tx_id,
            (SELECT symbol FROM pnl_calc ORDER BY pnl ASC LIMIT 1) AS min_symbol;
        """

    result = await session.execute(text(sql))
    row = result.fetchone()

    if row:
        max_pnl, max_tx_id, max_symbol, min_pnl, min_tx_id, min_symbol = row
        max_pnl = max_pnl if max_pnl is not None else 0.0
        min_pnl = min_pnl if min_pnl is not None else 0.0
        return max_pnl, min_pnl, max_tx_id, max_symbol, min_tx_id, min_symbol
    else:
        return 0.0, 0.0, None, None, None, None


async def get_total_pnl_sql(session: AsyncSession) -> float:
    """
    Method to calculate the sum of profit and loss (PnL) using SQL query
    :param session: session to connect to the database
    :return: total PnL
    """
    sql = """
           SELECT
               SUM(closed."baseTokenQuantity" - open."baseTokenQuantity") AS total_pnl
           FROM trades open
           JOIN trades closed 
               ON open.trade_position_id = closed.trade_position_id
           WHERE open.trade_type = 'open'
             AND closed.trade_type = 'closed';
       """

    result = await session.execute(text(sql))
    total_pnl = result.scalar()

    return total_pnl if total_pnl is not None else 0.0


async def get_total_profit_shared(session: AsyncSession) -> float:
    """
    Method to calculate the total profit shared with users
    :param session: session to connect to the database
    :return: total profit shared
    """
    stmt = (
        select(func.sum(Sharing.amount))
    )

    result = await session.execute(stmt)
    count = result.scalar_one()
    return count


async def calculate_total_sharing_usdt(session: AsyncSession) -> float:
    """
    Calculate the total value in USDT of all sharing tokens by summing
    the product of 'amount' and 'solana_price' for each Sharing record.

    Args:
        session (AsyncSession): The async database session.

    Returns:
        float: The total value in USDT. Returns 0.0 if no records are found.
    """
    stmt = select(func.sum(Sharing.amount * Sharing.solana_price))
    result = await session.execute(stmt)
    total_value = result.scalar() or 0.0
    return total_value

def parse_trade(trade, token, user_wallet):
    if trade.trade_type == TradeTypeEnum.closed:
        token_symbol_spent = token.symbol
        token_symbol_got = "SOL"
        amount_spent = trade.quoteTokenQuantity
        amount_got = trade.baseTokenQuantity
        transaction_direction = "sell"
        token_spent_url = token.image_url
        token_got_url = SOL_IMAGE_URL
    else:
        token_symbol_spent = "SOL"
        token_symbol_got = token.symbol
        amount_spent = trade.baseTokenQuantity
        amount_got = trade.quoteTokenQuantity
        transaction_direction = "buy"
        token_spent_url = SOL_IMAGE_URL
        token_got_url = token.image_url

    return {
        "created_at": trade.created_at,
        "tx_id": trade.tx_id,
        "user_address": user_wallet,
        "token_symbol_spent": token_symbol_spent,
        "token_symbol_got": token_symbol_got,
        "amount_spent": amount_spent,
        "amount_got": amount_got,
        "type": transaction_direction,
        "token_spent_url": token_spent_url,
        "token_got_url": token_got_url,
    }

def parse_payment(payment, token, user_wallet):
    return {
        "created_at": payment.created_at,
        "tx_id": payment.tx_hash,
        "token_symbol": token.symbol,
        "user_address": user_wallet,
        "type": 'reject',
        "token_img_url": token.image_url,
    }

def parse_sharing(sharing, to_address):
    return {
        "created_at": sharing.created_at,
        "tx_id": sharing.tx_id,
        "from": str(solana_driver.get_address()),
        "type": 'transfer',
        "to": to_address,
        "amount": f'{sharing.amount:.9f}'
    }

async def get_user_transactions(session: AsyncSession, user_address: str):
    transactions = []

    trade_query = (
        select(Trade, Token)
        .join(Token, Token.id == Trade.token_id)
        .join(ChatActionExtension, Trade.chat_uuid == ChatActionExtension.uuid)
        .join(User, ChatActionExtension.user_id == User.id)
        .filter(User.wallet == user_address)
    )
    trade_result = await session.execute(trade_query)
    for trade, token in trade_result.all():
        transactions.append(parse_trade(trade, token, user_address))

    payment_query = (
        select(Payment, Token)
        .join(Token, Token.id == Payment.token_id)
        .join(ChatActionExtension, Payment.chat_uuid == ChatActionExtension.uuid)
        .join(User, ChatActionExtension.user_id == User.id)
        .filter(Payment.decision_type == DecisionTypeEnum.reject)
        .filter(User.wallet == user_address)
    )
    payment_result = await session.execute(payment_query)
    for payment, token in payment_result.all():
        transactions.append(parse_payment(payment, token, user_address))

    sharing_query = (
        select(Sharing)
        .join(User, Sharing.user_id == User.id)
        .filter(User.wallet == user_address)
    )
    sharing_result = await session.execute(sharing_query)
    for sharing in sharing_result.scalars().all():
        transactions.append(parse_sharing(sharing, user_address))
    for txn in transactions:
        if isinstance(txn["created_at"], datetime.datetime):
            if txn["created_at"].tzinfo is None:
                txn["created_at"] = pytz.UTC.localize(txn["created_at"])

    sorted_transactions = sorted(
        transactions,
        key=lambda txn: txn["created_at"],
        reverse=True
    )

    return sorted_transactions

async def get_agent_transactions(session: AsyncSession):
    transactions = []

    trade_query = (
        select(Trade, Token, User)
        .join(Token, Token.id == Trade.token_id)
        .join(ChatActionExtension, Trade.chat_uuid == ChatActionExtension.uuid)
        .join(User, ChatActionExtension.user_id == User.id)
    )
    trade_result = await session.execute(trade_query)
    for trade, token, user in trade_result.all():
        transactions.append(parse_trade(trade, token, user.wallet))

    payment_query = (
        select(Payment, Token, User)
        .join(Token, Token.id == Payment.token_id)
        .join(ChatActionExtension, Payment.chat_uuid == ChatActionExtension.uuid)
        .join(User, ChatActionExtension.user_id == User.id)
        .filter(Payment.decision_type == DecisionTypeEnum.reject)
    )
    payment_result = await session.execute(payment_query)
    for payment, token, user in payment_result.all():
        transactions.append(parse_payment(payment, token, user.wallet))

    sharing_query = (
        select(Sharing, User)
        .join(User, Sharing.user_id == User.id)
    )
    sharing_result = await session.execute(sharing_query)
    for sharing, user in sharing_result.all():
        transactions.append(parse_sharing(sharing, user.wallet))

    for txn in transactions:
        if isinstance(txn["created_at"], datetime.datetime):
            if txn["created_at"].tzinfo is None:
                txn["created_at"] = pytz.UTC.localize(txn["created_at"])


    sorted_transactions = sorted(
        transactions,
        key=lambda txn: txn["created_at"],
        reverse=True
    )

    return sorted_transactions


async def get_agent_rejections(session: AsyncSession):
    query = (
        select(Payment, Token, User)
        .join(Token, Token.id == Payment.token_id)
        .join(ChatActionExtension, Payment.chat_uuid == ChatActionExtension.uuid)
        .join(User, ChatActionExtension.user_id == User.id)
        .filter(Payment.decision_type == DecisionTypeEnum.reject)
    )
    result = await session.execute(query)
    rows = result.all()

    decisions = []
    for row in rows:
        payment, token, user = row
        decisions.append({
            "created_at": payment.created_at,
            "user_address": user.wallet,
            "token_symbol": token.symbol,
            "token_name": token.name,
            "token_logo_url": token.image_url,
        })

    return decisions


def get_agent_balance_in_sol():
    balance_in_lamports = solana_driver.get_agent_balance()
    balance_in_sol = balance_in_lamports / 10 ** 9
    return f"{balance_in_sol:.9f}"


async def get_trades_summary(session: AsyncSession, period: str):
    """
    Returns a summary of open and closed trades grouped by a time period.

    Args:
        session: The AsyncSession to execute queries.
        period: One of "week", "month", or "year".
            - For "week": Groups by day of the current week.
            - For "month": Groups by week of the current month.
            - For "year": Groups by month of the current year.

    Returns:
        A list of dictionaries with each group period, open count, and closed count.
    """
    period = period.lower()
    if period not in {"week", "month", "year"}:
        raise ValueError("Invalid period. Choose one of: week, month, year.")

    today = datetime.date.today()

    if period == "week":
        start_date = today - datetime.timedelta(days=today.weekday())
        end_date = start_date + datetime.timedelta(days=7)
        group_field = func.date_trunc("day", Trade.created_at)
    elif period == "month":
        start_date = today.replace(day=1)
        last_day = calendar.monthrange(today.year, today.month)[1]
        end_date = today.replace(day=last_day) + datetime.timedelta(days=1)
        group_field = func.date_trunc("week", Trade.created_at)
    elif period == "year":
        start_date = today.replace(month=1, day=1)
        end_date = today.replace(month=12, day=31) + datetime.timedelta(days=1)
        group_field = func.date_trunc("month", Trade.created_at)

    open_count = (
        func.count()
        .filter(Trade.trade_type == TradeTypeEnum.open)
        .label("open_count")
    )

    closed_count = (
        func.count()
        .filter(Trade.trade_type == TradeTypeEnum.closed)
        .label("closed_count")
    )

    stmt = (
        select(group_field.label("period"), open_count, closed_count)
        .where(Trade.created_at >= start_date, Trade.created_at < end_date)
        .group_by(group_field)
        .order_by(group_field)
    )

    result = await session.execute(stmt)
    rows = result.all()

    summary = []
    for row in rows:
        period_label = row.period.isoformat() if row.period else None
        summary.append({
            "period": period_label,
            "open_count": int(row.open_count or 0),
            "closed_count": int(row.closed_count or 0)
        })

    return summary


async def get_trades_summary_general(session: AsyncSession):
    """
    Returns total counts of open and closed trades.

    Args:
        session: The AsyncSession to execute queries.

    Returns:
        List of dictionaries:
        [
            {"type": "closed", "num": 150},
            {"type": "open", "num": 200}
        ]
    """
    stmt = (
        select(
            Trade.trade_type.label("type"),
            func.count().label("num")
        )
        .group_by(Trade.trade_type)
        .order_by(Trade.trade_type)
    )

    result = await session.execute(stmt)
    return [{"type": row.type, "num": int(row.num)} for row in result]


async def get_agent_balance_summary(session: AsyncSession, period: str):
    """
    Returns agent balance values at specific time checkpoints grouped by a time period.

    Args:
        session: The AsyncSession to execute queries.
        period: One of "5min", "hour", "week", "month", or "year".
            - For "5min": Values are retrieved at 5-minute intervals.
            - For "hour": Values are retrieved at hourly intervals.
            - For "week": Values are retrieved at daily intervals for the current week.
            - For "month": Values are retrieved at weekly intervals for the current month.
            - For "year": Values are retrieved at monthly intervals for the current year.

    Returns:
        A list of dictionaries containing period and value at the checkpoint.
    """
    period = period.lower()
    if period not in {"5min", "hour", "week", "month", "year"}:
        raise ValueError("Invalid period. Choose one of: 5min, hour, week, month, year")

    now = datetime.datetime.now()
    today = datetime.date.today()

    if period == "5min":
        start_date = now - datetime.timedelta(hours=2)
        end_date = now
        group_field = func.date_trunc("minute", AgentBalanceChange.created_at)
    elif period == "hour":
        start_date = now - datetime.timedelta(days=1)
        end_date = now
        group_field = func.date_trunc("hour", AgentBalanceChange.created_at)
    elif period == "week":
        start_date = today - datetime.timedelta(days=today.weekday())
        end_date = start_date + datetime.timedelta(days=7)
        group_field = func.date_trunc("day", AgentBalanceChange.created_at)
    elif period == "month":
        start_date = today.replace(day=1)
        last_day = calendar.monthrange(today.year, today.month)[1]
        end_date = today.replace(day=last_day) + datetime.timedelta(days=1)
        group_field = func.date_trunc("week", AgentBalanceChange.created_at)
    else:
        #year
        start_date = today.replace(month=1, day=1)
        end_date = today.replace(month=12, day=31) + datetime.timedelta(days=1)
        group_field = func.date_trunc("month", AgentBalanceChange.created_at)

    subquery = (
        select(
            AgentBalanceChange.created_at,
            AgentBalanceChange.amount,
            group_field.label("period"),
            func.row_number()
            .over(partition_by=group_field, order_by=AgentBalanceChange.created_at.desc())
            .label("row_number")
        )
        .where(
            AgentBalanceChange.created_at >= start_date,
            AgentBalanceChange.created_at < end_date
        )
        .subquery()
    )

    stmt = (
        select(subquery.c.period, subquery.c.amount)
        .where(subquery.c.row_number == 1)
        .order_by(subquery.c.period)
    )

    result = await session.execute(stmt)
    rows = result.all()

    summary = [{
        "period": row.period.isoformat() if row.period else None,
        "value": float(row.amount or 0),
    } for row in rows]

    return summary




async def get_assets_summary(session: AsyncSession):
    query = (
        select(
            Trade.baseTokenQuantity,
            Token
        )
        .join(Token, Token.id == Trade.token_id)
        .join(TradePosition, TradePosition.id == Trade.trade_position_id)
        .filter(Token.amount > 0)
        .filter(Trade.trade_type == TradeTypeEnum.open.value)
        .filter(TradePosition.is_open == True)
    )

    result = await session.execute(query)
    token_records = result.all()

    balance_sol = float(get_agent_balance_in_sol())
    token_totals = defaultdict(float)

    for base_token_quantity, token in token_records:
        token_totals[token.token_address] += float(base_token_quantity)

    total_amount = balance_sol + sum(token_totals.values())
    summary = []

    for token_address, total_quantity in token_totals.items():
        token = next(t for _, t in token_records if t.token_address == token_address)

        token_percentage = (total_quantity / total_amount) * 100
        summary.append(
            {
                "token_symbol": token.symbol,
                "address": token.token_address,
                "percentage_in_portfolio": f'{token_percentage:.2f}',
                "amount": f'{token.amount:.{token.decimals}f}',
            }
        )

    sol_percentage = (balance_sol / total_amount) * 100
    summary.append(
        {
            "token_symbol": "SOL",
            "address": 'So11111111111111111111111111111111111111112',
            "percentage_in_portfolio": f'{sol_percentage:.2f}',
            "amount": f'{balance_sol:.9f}',
        }
    )

    return summary

async def get_dashboard_stats(session: AsyncSession) -> dict:
    """
    Fetch all dashboard portfolio (shilling message count, total trades,
    average PnL, total PnL, total shared profit in SOL and USDT) in a single query.

    Args:
        session (AsyncSession): The async database session.

    Returns:
        dict: A dictionary containing all dashboard portfolio.
    """
    sql = """
    WITH profit_calc AS (
        SELECT
            closed."baseTokenQuantity" - open."baseTokenQuantity" AS pnl
        FROM trades AS open
        JOIN trades AS closed
          ON open.trade_position_id = closed.trade_position_id
        WHERE open.trade_type = 'open'
          AND closed.trade_type = 'closed'
    )
    SELECT
        -- Count of shilling messages
        (SELECT SUM(cae.user_message_count)
         FROM chatactionextensions AS cae
         WHERE cae.action = :shilling_action) AS message_count,

        -- Total trades count
        (SELECT COUNT(*) FROM trades) AS total_trades,

        -- Average PnL
        (SELECT AVG(pnl) FROM profit_calc) AS avg_pnl,

        -- Total PnL
        (SELECT SUM(pnl) FROM profit_calc) AS total_pnl,

        -- Total profit shared
        (SELECT SUM(sh.amount) FROM sharings AS sh) AS shared_pnl_sol,

        -- Total profit shared in USDT
        (SELECT SUM(sh.amount * sh.solana_price) FROM sharings AS sh) AS shared_pnl_usdt
    """
    result = await session.execute(text(sql), {"shilling_action": ActionParameter.shilling})
    row = result.fetchone()

    return {
        "message_count": row.message_count or 0,
        "total_trades": row.total_trades or 0,
        "avg_pnl": f"{row.avg_pnl:.9f}" if row.avg_pnl is not None else "0.000000000",
        "total_pnl": f"{row.total_pnl:.9f}" if row.total_pnl is not None else "0.000000000",
        "shared_pnl": {
            "sol": f"{row.shared_pnl_sol:.9f}" if row.shared_pnl_sol is not None else "0.000000000",
            "usdt": f"{row.shared_pnl_usdt:.2f}" if row.shared_pnl_usdt is not None else "0.00",
        },
    }
