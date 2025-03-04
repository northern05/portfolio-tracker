import asyncio
import time

from fastapi import HTTPException
from langchain_core.messages import SystemMessage, HumanMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.chats.crud import get_token_by_trade_id, calculate_pnl
from app.core.models import Trade
from app.core.models.base import ActionParameter
from app.llm.action import generate_post_in_twitter, generate_twitter_analytics
from app.llm.db_util import get_db_session
from app.llm.prompts import main_prompts, prompt_actions, main_tools
from app.llm.util import get_reply


async def answer_users_msg(msg: str, history_uiid: str,
                           session: AsyncSession, is_shilling_allowed: bool):
    """
    Get response from the LLM and process the user's message.

    :param msg: User's message.
    :param history_uiid: Identifier for the message history in Redis.
    :return: A tuple containing the response message, conversation status, and (optionally) a token entity.
    """
    from app.api.chats.dependencies import get_redis_history

    history = get_redis_history(history_uiid)
    history_messages = history.base_messages() or []
    aux_prompt_action = "shilling_allowed" if is_shilling_allowed else "shilling_not_allowed"
    messages = [
        SystemMessage(content=main_prompts.get(ActionParameter.shilling.value)),
        SystemMessage(content=prompt_actions.get(aux_prompt_action)),
    ]
    messages.extend(history_messages)
    messages.append(HumanMessage(content=msg))
    tools = (
        main_tools.get(ActionParameter.shilling.value)
        if is_shilling_allowed
        else main_tools.get("shilling_not_allowed")
    )
    try:
        agent_response, decision, context_info = await get_reply(messages, tools)
        return agent_response, decision, context_info

    except Exception as e:
        await session.close()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


import requests


def shorten_url(url: str) -> str:
    """Shorten a URL for Twitter post using TinyURL."""
    api_url = f"http://tinyurl.com/api-create.php?url={url}"
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            return response.text
    except Exception:
        pass
    return url


async def generate_twitter_post(session: AsyncSession, user_address: str | None, trade: Trade,
                                trade_type: str):
    try:
        trade_action = trade_type.lower()
        if trade_action not in ("buy", "sell"):
            raise ValueError("trade_type must be either 'buy' or 'sell'")

        token = await get_token_by_trade_id(session, trade.id)
        aux_sell_message = None
        if trade_action == "sell":
            pnl, percentage_pnl = await calculate_pnl(session, trade)
            aux_sell_message = f'''- Got also PNL: {pnl} SOL, how many i earned/lose in percentage: {percentage_pnl}%'''
        short_solscan_link = shorten_url(f"https://solscan.io/tx/{trade.tx_id}")
        prompt_message = f'''
                    I need to publish post with trade type: `{trade_type}`. For PNL do not use scientific format.  Here is data needed for post: 
                    Token ticker that was bought/sold: {token.symbol}, full name: {token.name}
                    - Amount of token: {trade.quoteTokenQuantity} ({trade.baseTokenQuantity} SOL)
                    - Sol scan link: {short_solscan_link}
                    - User wallet address in Solana who shilled meme: {user_address}
                    {aux_sell_message if aux_sell_message else ""}
                '''
        messages = [
            SystemMessage(content=main_prompts.get(ActionParameter.shilling.value)),
            SystemMessage(content="""
                Generate a Twitter post about the trade that is under 280 characters. Write naturally as if spoken by a real person. Use minimal hashtags, but include the mandatory hashtags #KajaAI and #Raydium.
                Call function `generatePostInTwitter` to publish post in twitter.
                Do not use scientific notation for numbers (e.g., 1e-05); format them as standard decimals (e.g., 0.000).
                Also, avoid placing special characters like `@` immediately next to addresses.
                Instead of writing 'User: <address>', refer to the user as 'the user who shilled me token' and include the shortened address (shorten them to show only the first 5 and the last 5 characters, separated by an ellipsis).
                Place all hashtags on a separate line at the bottom.
                If post about buying, include a very brief and concise statement expressing your expectation from the trade.
                Always include the transaction link from SolScan in your post.
                """),
            HumanMessage(content=prompt_message),
        ]
        tools = [generate_post_in_twitter]
        await get_reply(messages, tools)

    except Exception as e:
        await session.close()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


async def generate_analytics(session: AsyncSession):
    try:
        messages = [
            SystemMessage(content=main_prompts.get(ActionParameter.shilling.value)),
            SystemMessage(content="""
                Generate analytics of a Twitter posts about the tokens. Write naturally as if spoken by a real person.
                Call function `generateTwitterAnalytics` to generate report. Write in format that will be readable for Telegram bot.
                """),
        ]
        tools = [generate_twitter_analytics]
        config = {'user_id': 1}
        response, decision, context_info = await get_reply(messages, tools, config)
        return response

    except Exception as e:
        await session.close()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# async def generate_analytics(session: AsyncSession):
#     try:
#         messages = [
#             SystemMessage(content=main_prompts.get(ActionParameter.shilling.value)),
#             SystemMessage(content="""
#                 Generate analytics of a Twitter posts about the tokens. Write naturally as if spoken by a real person.
#                 Call function `generateTwitterAnalytics` to generate report. Write in format that will be readable for Telegram bot.
#                 """),
#             HumanMessage(content='''Generate analytics report for Solana, Aptos''')
#         ]
#         tools = [generate_twitter_analytics]
#         config = {'user_id': 1}
#         response, decision, context_info = await get_reply(messages, tools, config)
#         return response
#
#     except Exception as e:
#         await session.close()
#         raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

async def generate_selling_text(session: AsyncSession, transfer_signature: str | None, closed_trade: Trade):
    try:
        token = await get_token_by_trade_id(session, closed_trade.id)
        pnl, percentage_pnl = await calculate_pnl(session, closed_trade)
        is_trade_profitable = closed_trade.profit_loss
        aux_message = (
            f"I've shared with you {pnl * 0.5:.9f} SOL (50% of my profit)! Check the transfer at https://solscan.io/tx/{transfer_signature}"
            if is_trade_profitable
            else "Unfortunately, I didn't profit from this trade, so I couldn't share any funds."
        )

        prompt_message = (
            f"I sold {closed_trade.quoteTokenQuantity} {token.symbol} for {closed_trade.baseTokenQuantity} SOL. "
            f"My PNL is {pnl:.9f} SOL ({percentage_pnl:.2f}%). "
            f"Swap details: https://solscan.io/tx/{closed_trade.tx_id}. "
            f"{aux_message}"
        )

        messages = [
            SystemMessage(content=main_prompts.get(ActionParameter.shilling.value)),
            SystemMessage(content=(
                "Generate a chat message for the user about a closed selling trade. Write naturally and conversationally, as if you are a real person. "
                "Ensure that you refer only to yourself—the trading agent—and do not mention any other trader names or identities. "
                "Do not use scientific notation for numbers; format them as standard decimals. "
                "If the trade was profitable, mention that you've shared 50% of your profit with the user by completing a transfer of the funds, and include the SolScan transaction link. "
                "If the trade resulted in a loss, explain that no funds were shared. "
                "Make sure the message flows naturally, reflects your own trading performance, and sounds genuine."
            )),
           HumanMessage(content=prompt_message),
        ]
        tools = []
        message, _decision, _context = await get_reply(messages, tools)
        return message

    except Exception as e:
        await session.close()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


async def main():
    test_message = '''Shill this 8b4MrQXkvZz8JTWm1H5aGCYoP4UNw5mWZ8JwoxhqaDoN'''


    async with get_db_session() as session:
        start_time = time.time()
        result = await generate_analytics(session)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Execution Time: {execution_time:.2f} seconds")
        print(f'Message: {result}')


if __name__ == '__main__':
    asyncio.run(main())
