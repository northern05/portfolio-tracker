import datetime
import logging

import jsonpickle
from fastapi import Depends, HTTPException

from app.core.models import db_helper
from app.core.modules_factory import twitter_driver, redis_db, solana_driver
from utils.binance import fetch_solana_price_binance
from utils.dexscreener import fetch_dexscreener_data
from .schemas import ConnectTwitter
from .crud import *
from ..chats.crud import create_closed_trade, decrease_token_amount, get_agent_portfolio
from ..chats.dependencies import get_extended_chat_by_user
from ...core.models.base import ActionParameter
from ...llm.llm_service import generate_selling_text, generate_twitter_post


async def check_retwitts(
        session: AsyncSession = Depends(db_helper.scoped_session_dependency)
):
    response = []
    # select all users
    users = await get_all_twitter_users(session=session)
    twitter_id_user_id = {u.twitter_id: u.id for u in users}
    # query all twitter posts from
    posts = await get_twitter_posts(session=session)

    for post_id in posts:
        retwitted_users = twitter_driver.get_retwitters_by_post_id(post_id=post_id)
        for twitter_id in retwitted_users:
            if str(twitter_id) in twitter_id_user_id.keys():
                existing_retwitt = await check_existing_retwitted_post(
                    user_id=twitter_id_user_id.get(str(twitter_id)),
                    post_id=post_id,
                    session=session
                )
                if existing_retwitt:
                    continue
                credit = await create_users_retwitt(
                    session=session,
                    user_id=twitter_id_user_id.get(str(twitter_id)),
                    twitter_post_id=str(post_id)
                )
                response.append(credit.id)
    return response


async def sell_tokens(
        session: AsyncSession = Depends(db_helper.scoped_session_dependency)
):
    response = []

    open_trades = await get_all_tokens_to_sell(session=session)
    for open_trade, _amount, pool_address, user in open_trades:
        try:
            result = solana_driver.swap_base_token(pool_id=pool_address, amount=open_trade.quoteTokenQuantity)
            base_token_quantity, quote_token_quantity, tx_id, fee = result.get('amountOut'), result.get(
                'amountIn'), result.get('txId'), result.get('fee')
            logging.info(
                f'Swapped {quote_token_quantity} to {base_token_quantity} for {pool_address} with tx_id: {tx_id}')
            # Update portfolio
            closed_trade = await create_closed_trade(session=session, chat_uuid=open_trade.chat_uuid,
                                                     base_token_quantity=float(base_token_quantity),
                                                     quote_token_quantity=float(quote_token_quantity), tx_id=tx_id,
                                                     token_id=open_trade.token_id,
                                                     fee=float(fee))
            # Decrease amount of tokens in portfolio
            await decrease_token_amount(
                session=session,
                trade=closed_trade
            )
            transfer_transaction = None
            if closed_trade.profit_loss:
                # Transfer 50% to user
                sharing_amount_in_sol = closed_trade.baseTokenQuantity - open_trade.baseTokenQuantity
                sharing_amount = sharing_amount_in_sol * 500_000_000
                transfer_transaction = solana_driver.transfer_share_to_user(
                    user_address=user.wallet,
                    amount=int(sharing_amount)
                )
                # Fetch solana price
                solana_price = fetch_solana_price_binance()
                # Save sharing info to DB
                await create_sharing(
                    session=session,
                    user_id=user.id,
                    trade_id=closed_trade.id,
                    amount=float(sharing_amount_in_sol),
                    tx_id=transfer_transaction,
                    solana_price=solana_price
                )

            else:
                # Generate LLM text and save to chat
                chat = await get_extended_chat_by_user(action_param=ActionParameter.shilling, user=user, session=session)
                llm_message = await generate_selling_text(session=session, closed_trade=closed_trade,transfer_signature=transfer_transaction)
                timestamp = int(datetime.now().timestamp() * 1000)
                chat.history.append({
                    "role": "system",
                    "content": llm_message,
                    "timestamp": timestamp,
                    "is_approved": False,
                    "decision": "discuss",
                    "aux_data": None
                })
                await redis_db.set(chat.uuid, jsonpickle.encode(chat.history))

            # Publish result in Twitter
            try:
                await generate_twitter_post(session=session, trade=closed_trade,
                                            trade_type="sell", user_address=user.wallet)
            except Exception as e:
                logging.critical(f'Failed to publish post in Twitter about selling token. Error: {e}')
                error_data = {
                    "error": str(e),
                    "trade_data": {
                        "id": closed_trade.id,
                    }
                }
                logging.error(error_data)
                await redis_db.set(f'error_post_sell_{tx_id}', jsonpickle.encode(error_data))
        except Exception as e:
            logging.critical(f'Error occurs: {e} while selling token.')
            await session.close()
            raise HTTPException(status_code=500, detail=f"Failed to swap token")

    return response

async def log_agent_balance(
        session: AsyncSession = Depends(db_helper.scoped_session_dependency)
):
    response = []
    agent_balance_in_lamport = solana_driver.get_agent_balance()
    agent_balance_in_sol = float(agent_balance_in_lamport / 10 ** 9)
    # Extract tokens
    amount_of_tokens_in_sol = float(0)
    tokens = await get_agent_portfolio(session=session)
    for token in tokens:
        dexscreener_data = fetch_dexscreener_data(token.token_address)[0]
        price = float(dexscreener_data['priceNative'])
        amount_of_tokens_in_sol += float(token.amount) * price
    amount = agent_balance_in_sol + amount_of_tokens_in_sol

    await create_agent_balance_change(session=session, amount=amount, sol_amount=agent_balance_in_sol)
    return response


async def connect_twitter(
        data: ConnectTwitter,
        session: AsyncSession = Depends(db_helper.scoped_session_dependency)
):
    result = await update_user(session=session, wallet=data.wallet_address, twitter_id=data.twitter_id)
    return result
