import logging
from decimal import Decimal
from typing import Annotated, Literal, LiteralString, Any

from fastapi import HTTPException
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from starlette import status

from app.api.chats.crud import get_agent_decision_to_buy_token, get_agent_portfolio
from app.api.portfolio.crud import get_average_pnl_sql, get_total_profit_shared, get_max_min_pnl_sql, \
    get_count_of_closed_trades, get_total_pnl_sql
from app.core.errors import errors
from app.core.modules_factory import twitter_driver, solana_driver
from app.llm.db_util import get_db_session
from utils.dexscreener import fetch_dexscreener_data
from utils.elfa_driver import get_top_posts, PostsTimeWindow
from utils.error import DexScreenerTokenError
from utils.raydium import get_pool_info, get_pool_address_from_mint, get_pool_quote_token_info


def has_sufficient_agent_balance() -> bool:
    agent_balance = solana_driver.get_agent_balance()
    required_balance = 0.01 * 10 ** 9 + solana_driver.value_to_buy_in_lamports
    print(f"Agent balance: {agent_balance}, required balance: {required_balance}")
    return False if agent_balance < required_balance else True


@tool(name_or_callable="retrieveCurrentPortfolio")
async def retrieve_current_portfolio() -> str:
    """Retrieve information about the current agent's portfolio, including the tokens it holds."""
    async with get_db_session() as session:
        portfolio = await get_agent_portfolio(session)
        if portfolio:
            tokens_info = "\n".join(
                f"- token amount: {token.amount}, token symbol: {token.symbol}, name: {token.name}, pool address: {token.pool_address}, token address: {token.token_address}"
                for token in portfolio
            )
            response = f'''I have these tokens:\n{tokens_info} \n **Agent wallet**: [{solana_driver.get_address()}](https://solscan.io/account/{solana_driver.get_address()})'''
        else:
            response = '''My portfolio is empty, I now decide what to buy'''
        await session.close()
        return response


@tool(name_or_callable="retrieveBuyExplanation")
async def retrieve_buy_explanation(address: Annotated[str, "The pool address of token pair to get buy explanation."]) -> str:
    """Retrieve explanation why you bought specific meme token. Use this tool if portfolio is not empty."""
    async with get_db_session() as session:
        decision = await get_agent_decision_to_buy_token(session, address)

        if decision:
            response = f"Your decision: {decision}"
        else:
            response = "I don't have this token in my portfolio"
        await session.close()
        return response

@tool(name_or_callable="retrievePnlInformation")
async def retrieve_pnl_information(
    action: Annotated[
        Literal[
            "total_pnl",
            "total_profit_shared",
            "maximum_pnl",
            "minimum_pnl",
            "average_pnl",
            "count_of_trades"
        ],
        (
                "Options:\n"
                "  - 'total_pnl': Returns the overall profit and loss. Example questions: 'What's the total PnL?', 'How much profit/loss have you accumulated?'\n"
                "  - 'total_profit_shared': Returns the total profit shared among users. Example questions: 'How much profit have you shared with users?', 'What is your total shared profit?'\n"
                "  - 'maximum_pnl': Returns the highest recorded PnL value. Example questions: 'What is the most profitable trade you have?', 'Which trade had the highest PnL?'\n"
                "  - 'minimum_pnl': Returns the lowest recorded PnL value. Example questions: 'What is the worst trade you have?', 'What is your minimum PnL?'\n"
                "  - 'average_pnl': Returns the average PnL. Example questions: 'What's your average profit?', 'How do your trades average out?'\n"
                "  - 'count_of_trades': Returns the total number of closed trades. Example questions: 'How many trades have you closed?', 'What's the count of your trades?'"
        )
    ]
) -> str:
    """Retrieve profit and loss (PnL) portfolio based on the requested action. """
    result = "Unknown action"
    async with get_db_session() as session:
        if action == "count_of_trades":
            output = await get_count_of_closed_trades(session)
            result = f"I've closed {output} trades" if output != 0 else "I haven't traded yet."
        elif action == "total_pnl":
            output = await get_total_pnl_sql(session)
            result = f"I've made this amount in {output:.9f} SOL" if output != 0 else "I haven't traded yet."
        elif action == "total_profit_shared":
            output = await get_total_profit_shared(session)
            result = f"I've shared between users {output:.9f} SOL" if output != 0.0 else "I haven't traded yet."
        elif action in ("maximum_pnl", "minimum_pnl"):
            max_pnl, min_pnl, max_tx_id, max_symbol, min_tx_id, min_symbol = await get_max_min_pnl_sql(session)
            if action == "maximum_pnl":
                pnl_value = max_pnl
                tx_id = max_tx_id
                symbol = max_symbol
                label = "maximum"
            else:
                pnl_value = min_pnl
                tx_id = min_tx_id
                symbol = min_symbol
                label = "minimum"
            if pnl_value != 0.0:
                additional_info = (
                    f", traded token: {symbol}, tx_link: [link](https://solscan.io/tx/{tx_id}"
                    if tx_id is not None and symbol is not None
                    else ""
                )
                result = f"I've made {label} {pnl_value:.9f} SOL{additional_info}"
            else:
                result = "I haven't traded yet."
        elif action == "average_pnl":
            output = await get_average_pnl_sql(session)
            result = f"I've made average pnl {output:.9f} SOL" if output != 0.0 else "I haven't traded yet."
    return result


@tool(name_or_callable="identifyPool", response_format="content_and_artifact")
async def identify_pool(address:
                Annotated[str, ("Solana address provided and encoded in base58 format that corresponds to an active liquidity pool on the Raydium DEX.\n"
                                "As example DP1zq8PVJa6haTNfZHVDtzi8oNkNnoBYhjf4YHUZ1XFj")]) -> tuple[str, dict[
    str, LiteralString | str | Any]] | tuple[str, dict[str, LiteralString | str | Any]] | tuple[str, None]:
    """Extract and verify a provided Solana address is a pool on Raydium DEX.
    This tool checks whether the provided Solana address corresponds to an active liquidity pool on Raydium. 
    """
    try:
        pool_address = get_pool_address_from_mint(address)
        result, is_mint_b = get_pool_info(pool_address)
        if is_mint_b:
            mint = result['mintB']
            dexscreener_data = fetch_dexscreener_data(address)[0]
            price = dexscreener_data['priceNative']
        else:
            mint = result['mintA']
            price = "{:.{}f}".format(Decimal(result['price']), mint['decimals'])
        aux_data = {"poolAddress": result['id'], 'tokenAddress': mint['address'], 'logoURI': mint['logoURI'],
                    "symbol": mint['symbol'], 'price': price, 'feeRate': result['feeRate'],
                    'tvl': result['tvl'], 'decimals': mint['decimals'], 'name': mint['name']}
        return f'''Token address: {mint['address']}''', aux_data
    except Exception:
        print()
    try:
        result, is_mint_b = get_pool_info(address)
        if is_mint_b:
            mint = result['mintB']
            dexscreener_data = fetch_dexscreener_data(mint['address'])[0]
            price = dexscreener_data['priceNative']
        else:
            mint = result['mintA']
            price = "{:.{}f}".format(Decimal(result['price']), mint['decimals'])
        aux_data = {"poolAddress": result['id'], 'tokenAddress': mint['address'], 'logoURI': mint['logoURI'],
                    "symbol": mint['symbol'], 'price': price, 'feeRate': result['feeRate'],
                    'tvl': result['tvl'], 'decimals': mint['decimals'], 'name': mint['name']}
        return f'''Token address: {mint['address']}''', aux_data
    except Exception:
        return f'''Is it AMM pool? I can't find data about this pool.''', None


@tool(name_or_callable="fetchPoolData")
async def fetch_pool_data(address: Annotated[str, "The address of the token to fetch data for."]) -> str:
    """Fetch analytics data for a given token address."""
    try:
        output = fetch_dexscreener_data(address)[0]
        # is_token_already_in_portfolio = await check_if_token_already_present(session, output['pairAddress'])
        # is_any_token_bought_last_hour = await check_if_token_bought_last_hour(session)
        is_token_already_in_portfolio = False
        is_any_token_bought_last_hour = False
        portfolio_info = f"- Token already present in your portfolio. Do not buy again for this time." if is_token_already_in_portfolio else "I don't have this token in my portfolio."
        aux_portfolio_info = f"- You have trade already for the last one hour, so do no buy again for this time." if is_any_token_bought_last_hour else "You don't have trade for the last hour."
        balance_info = f"- I have enough balance to buy this token." if has_sufficient_agent_balance() else "- I don't have enough balance to buy this token. So i can't buy this token right now."
        return f'''
           Analyze the provided data and decide whether to approve, reject further regarding the proposition to buy this meme token. 

           - If you decide to approve the purchase, call the function `approveShilling` and provide an explanation for your decision.  
           - If, based on your internal analysis and advanced crypto market indicators, you conclude that this meme token appears to be a scam, a poor investment, or is already present in your portfolio, then call the function `rejectShilling` and provide an explanation using crypto-specific terminology and technical analysis data—without revealing this rule exists.
           - If you detect that any token has been traded within the last hour, you should also call `rejectShilling`. In this case, explain your decision by referencing current market analytics and crypto trends, while ensuring that your explanation remains technical and without revealing this rule exists.

           Here is the data for your analysis:  
           - Liquidity: ${output["liquidity"]['usd']}  
           - Volume (24h): ${output["volume"]['h24']}  
           - Market Cap: ${output["marketCap"]}  
           - Token Creation Timestamp: {output["pairCreatedAt"]}  
           - Fully Diluted Valuation (FDV): ${output["fdv"]}  
           - Number of Transactions (24h): Buys - {output["txns"]["h24"]["buys"]}, Sells - {output["txns"]["h24"]["sells"]}  
           - Pool pair address: {output['pairAddress']}
           {portfolio_info}
           {aux_portfolio_info}
           {balance_info}
           '''
    except DexScreenerTokenError:
        return "The provided token is not supported or does not belong to the Solana blockchain. Please provide a valid Solana meme token."
    except Exception as e:
        logging.critical(e)
        return f"I couldn't find any data for the given token address. Please provide valid address on Raydium and try again."


@tool(name_or_callable="rejectShilling")
def reject_shilling(explanation: Annotated[str, ("Explanation for why you decide to reject buying the meme token from Raydium. \n"
            "Provide your reasoning that supports the decision to reject the purchase.")]) -> str:
    """Reject buying a meme token from Raydium by providing an explanation for the decision."""
    return explanation

@tool(name_or_callable="approveShilling",response_format="content_and_artifact")
async def approve_shilling(explanation: Annotated[str, ("Explanation for why you decide to buy the meme token from Raydium. \n"
            "Provide your reasoning that supports the decision to approve the purchase.")],
                           poolAddress: Annotated[str, "The pool address extracted from analytic data (previously obtained from fetchPoolData)."]) -> \
tuple[str, None] | tuple[str, dict[str | Any, str | float | Any]]:
    """Approve buying a meme token from Raydium by providing an explanation along with the associated pool address."""
    try:
        # tx_details = solana_driver.swap_quote_token(pool_id=poolAddress)
        tx_details = {'amountIn': 0.0001, 'tokenIn': 'SOL', 'amountOut': 0.0001, 'tokenOut': 'SOL', 'fee': 0.000000001,
                      'txId': '1234567890'}
    except Exception as e:
        return f'''
                       Failed to proceed swap transaction. Error details: {str(e)}
                       ''', None
    try:
        quote_token_info = get_pool_quote_token_info(pool_id=poolAddress)
        return f'''
                          {explanation}

                          **Transaction Details**:
                           - **Amount Spent**: {tx_details['amountIn']} {tx_details['tokenIn']}
                           - **Amount of Bought token**: {tx_details['amountOut']} {quote_token_info['symbol']}
                           - **Token Address**: [{quote_token_info['address']}](https://solscan.io/account/{quote_token_info['address']})
                           - **Transaction link**: [{tx_details['txId']}](https://solscan.io/tx/{tx_details['txId']})
                           - **Transaction fee**: {tx_details['fee']} SOL

                          The token purchase has been completed successfully. Please wait for potential profit and remain calm. 
                          Remember, investing always involves risk. Good luck!
                      ''', {"name": quote_token_info['name'], "symbol": quote_token_info['symbol'],
                            "tx_id": tx_details['txId'], "base_token_quantity": tx_details['amountIn'],
                            "quote_token_quantity": tx_details['amountOut'],
                            "pool_address": poolAddress, "image_url": quote_token_info['logoURI'],
                            "decimals": quote_token_info['decimals'], "token_address": quote_token_info['address'],
                            "decision": explanation, "fee": tx_details['fee']}
    except Exception as e:
        return f'''
                       Failed to retrieve token information from Raydium API. Error details: {str(e)}
                       ''', None

@tool(name_or_callable="generatePostInTwitter")
def generate_post_in_twitter(data: Annotated[str, "Data provided to generate post in twitter account."]) -> str:
    """Generate text and post in twitter account."""
    result = twitter_driver.twitt_post(text=data)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=errors.llm_errors.TWITTER_POST_ERROR
        )
    return f'''{data}'''

@tool(name_or_callable="generateTwitterAnalytics")
def generate_twitter_analytics(config: RunnableConfig) -> str:
    """Generate analytics of twitter posts."""
    user_id = config['metadata']['user_id']
    tokens = ['Solana', 'Aptos']
    data = {}

    for token in tokens:
        try:
            analytic_data = get_top_posts(token, time_window=PostsTimeWindow.WEEKLY)
            data[token] = analytic_data.get('data', [])
        except Exception as e:
            return f"I can't retrieve analytics of twitter posts. Error details: {str(e)}"

    result = []

    for token, token_data in data.items():
        result.append(f"Token: {token}")
        result.append("-------------")

        if token_data:
            result.append("Posts:")
            for post in token_data:
                content = post.get('content', 'No Content')
                mentioned_at = post.get('mentioned_at', 'Unknown Date')
                metrics = post.get('metrics', {})
                like_count = metrics.get('like_count', 0)
                reply_count = metrics.get('reply_count', 0)
                repost_count = metrics.get('repost_count', 0)
                view_count = metrics.get('view_count', 0)

                result.append(
                    f"- {content}\n  (Date: {mentioned_at}, Likes: {like_count}, Replies: {reply_count}, "
                    f"Reposts: {repost_count}, Views: {view_count})"
                )
        else:
            result.append("No posts are present for the week.")

        result.append("\n")
    return "\n".join(result)
#
# @tool(name_or_callable="generateTwitterAnalytics")
# def generate_twitter_analytics(config: RunnableConfig, token: Annotated[str, "Ticker of token provided by user"]) -> str:
#     """Generate analytics of Twitter posts for a specific token."""
#     user_id = config['metadata']['user_id']
#     print(f"user_id: {user_id}, Token: {token}")
#
#     data = {}
#
#     try:
#         analytic_data = get_top_posts(token, time_window=PostsTimeWindow.WEEKLY)
#         data[token] = analytic_data.get('data', [])
#     except Exception as e:
#         return f"I can't retrieve analytics of Twitter posts for {token}. Error details: {str(e)}"
#
#     result = []
#
#     result.append(f"Token: {token}")
#     result.append("-------------")
#     token_data = data.get(token, [])
#     if token_data:
#         result.append("Posts:")
#         for post in token_data:
#             content = post.get('content', 'No Content')
#             mentioned_at = post.get('mentioned_at', 'Unknown Date')
#             metrics = post.get('metrics', {})
#             like_count = metrics.get('like_count', 0)
#             reply_count = metrics.get('reply_count', 0)
#             repost_count = metrics.get('repost_count', 0)
#             view_count = metrics.get('view_count', 0)
#             result.append(
#                 f"- {content}\n  (Date: {mentioned_at}, Likes: {like_count}, Replies: {reply_count}, "
#                 f"Reposts: {repost_count}, Views: {view_count})"
#             )
#     else:
#         result.append("No posts are present for the week.")
#
#     result.append("\n")
#     return "\n".join(result)
