import logging
import os
from typing import Union

import requests
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram import Router, F, types, Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest
import re

WALLET_REGEX = {
    "Ethereum / BSC / Polygon (EVM-based)": r"^0x[a-fA-F0-9]{40}$",
    "Bitcoin": r"^(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}$",
    "Solana": r"^[1-9A-HJ-NP-Za-km-z]{32,44}$",
    "Tron (TRC-20)": r"^T[a-zA-Z0-9]{33}$",
    "Ripple (XRP)": r"^r[0-9a-zA-Z]{24,34}$",
    "Dogecoin": r"^D{1}[5-9A-HJ-NP-U]{1}[1-9A-HJ-NP-Za-km-z]{32,34}$",
    "Litecoin": r"^[LM3][a-km-zA-HJ-NP-Z1-9]{26,33}$",
    "Cardano (ADA)": r"^addr1[a-z0-9]+$",
}

TOKEN: str = os.environ.get('TG_TOKEN', "7540334723:AAFGudo28Myy4ltPmZLz3jhODPY4iVrkRG4")
API_URL: str = os.environ.get('BASE_SITE', "https://api.agent.zpoken.dev/portfolio_tracker/api/v1/portfolio")
API_KEY: str = os.environ.get('TG_API_KEY', "tg_api_key")
MAX_BUTTONS_PER_MESSAGE = 10

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode='Markdown'))
dp = Dispatcher()

self_id = 7540334723


def get_similar_tokens(symbol: str, token_id: str = None):
    params = {"asset_symbol": symbol}
    if token_id:
        params.update({"token_id": token_id})
    result = requests.get(f"{API_URL}/similar_assets", params=params)
    return result.json()


def validate_wallet(address: str):
    for blockchain, pattern in WALLET_REGEX.items():
        if re.match(pattern, address):
            return True, f"✅ Valid {blockchain} wallet!"
    return False, "❌ Invalid wallet address."


def format_market_cap(market_cap):
    """Formats the market cap to a human-readable format (B, M, K)."""
    if market_cap >= 1_000_000_000:  # Billion
        return f"MCap {market_cap / 1_000_000_000:.1f}B"
    elif market_cap >= 1_000_000:  # Million
        return f"MCap {market_cap / 1_000_000:.1f}M"
    elif market_cap >= 1_000:  # Thousand
        return f"MCap {market_cap / 1_000:.1f}K"
    else:
        return f"MCap {market_cap}"


tg_router = Router()
dp.include_router(tg_router)


class PortfolioState(StatesGroup):
    entering_wallet = State()
    choosing_coin = State()
    enter_coin = State()
    choosing_frequency = State()


@tg_router.startup()
async def on_startup(bot: Bot):
    await set_bot_commands(bot)


async def set_bot_commands(bot: Bot):
    commands = [
        types.BotCommand(command="start", description="Start the bot"),
        types.BotCommand(command="add_wallet", description="Add your crypto wallet"),
        types.BotCommand(command="my_portfolio", description="View your portfolio"),
        types.BotCommand(command="get_report_menu", description="Get a 7-day report for a coin"),
        types.BotCommand(command="help", description="Show help menu")
    ]
    await bot.set_my_commands(commands)


@tg_router.message(Command("help"))
async def show_commands(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📌 Start", callback_data="cmd_start")],
            [InlineKeyboardButton(text="💼 Add Wallet", callback_data="cmd_add_wallet")],
            [InlineKeyboardButton(text="📊 View Portfolio", callback_data="cmd_my_portfolio")],
            [InlineKeyboardButton(text="📉 Get Report", callback_data="cmd_get_report")],
            [InlineKeyboardButton(text="ℹ️ Help", callback_data="cmd_help")]
        ]
    )
    await message.answer("🔹 Choose a command:", reply_markup=keyboard)


@tg_router.callback_query(F.data.startswith("cmd_"))
async def handle_command_callback(callback: types.CallbackQuery):
    command_map = {
        "cmd_start": "/start - Start the bot",
        "cmd_add_wallet": "/add_wallet - Add your crypto wallet",
        "cmd_my_portfolio": "/my_portfolio - View your portfolio",
        "cmd_get_report": "/get_report_menu - Get a 7-day report for a coin",
        "cmd_help": "/help - Show help message"
    }
    command = command_map.get(callback.data)
    if command:
        await callback.message.answer(f"Executing {command}...")  # Optional message
        await callback.answer()  # Closes the loading animation
        await tg_router.message.dispatch(
            types.Message(chat=callback.message.chat, text=command, from_user=callback.from_user))


@tg_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(PortfolioState.entering_wallet)
    await message.answer("Hi! I will tell you all news about cryptocurrency you want!")
    await message.answer("Enter your crypto-wallet to create your own portfolio:")


@tg_router.message(PortfolioState.entering_wallet)
async def save_wallet(message: types.Message, state: FSMContext):
    wallet = message.text.strip()
    result, msg = validate_wallet(address=wallet)
    if result:
        response = requests.post(f"{API_URL}/connect_telegram",
                                 json={"telegram_id": str(message.from_user.id), "wallet": wallet})
        if response.status_code == 200:
            await state.set_state(PortfolioState.choosing_coin)
            await message.answer(
                "Wallet saved! Enter cryptocurrency you want to see news (for example: BTC, ETH, SOL):")
        else:
            await message.answer("Error wallet adding. Try another one time.")
    else:
        await message.answer(msg)
        await message.answer("Enter your crypto-wallet to create your own portfolio:")
        await state.set_state(PortfolioState.entering_wallet)


@tg_router.message(PortfolioState.choosing_coin)
async def process_token(message: types.Message, state: FSMContext):
    symbol = message.text.upper()
    similar_tokens = get_similar_tokens(symbol=symbol)
    if not similar_tokens:
        await message.answer("No similar assets found. Please enter a different character:")
        return

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text=f"{str(token.get('symbol'))} {format_market_cap(token.get('market_cap'))}$ {token.get('token_id')}")] for
            token in similar_tokens],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("Choose currency:", reply_markup=keyboard)
    await state.set_state(PortfolioState.enter_coin)
    await state.update_data(token=symbol)


@tg_router.message(PortfolioState.enter_coin)
async def add_coins_to_portfolio(message: types.Message, state: FSMContext):
    symbol = message.text.split()[0].upper()
    token_id = message.text.split()[3]
    similar_token = get_similar_tokens(symbol=symbol, token_id=token_id)
    if symbol != similar_token.get("symbol"):
        await message.answer("No similar assets found. Please enter a different character:")
        return
    response = requests.post(f"{API_URL}", json={"telegram_id": str(message.from_user.id), "symbol": symbol, "twitter": similar_token.get('twitter')})

    if response.status_code == 200:
        await state.clear()
        await message.answer(f"Coin {symbol} added to your portfolio! 🎉")
    else:
        await message.answer("Failed. Try later.")


@tg_router.message(Command("my_portfolio"))
async def edit_portfolio_menu(message: types.Message):
    telegram_id = message.from_user.id if message.from_user.id != self_id else message.chat.id
    response = requests.get(f"{API_URL}", params={"telegram_id": str(telegram_id)})

    if response.status_code == 200:
        data = response.json()
        coins = [coin.get("symbol") for coin in data]

        if not coins:
            await message.answer(
                "Your portfolio is empty, you can add wallet with **/add_wallet**, and then add coins with **/add_coin**.",
                parse_mode='Markdown')
            return

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="➖ Delete", callback_data="delete_menu"),
                 InlineKeyboardButton(text="➕ Add coin", callback_data="add_coin")],
                [InlineKeyboardButton(text="📊 Get report", callback_data="get_report_menu")],
                [InlineKeyboardButton(text="📊 Get total report", callback_data="get_total_report")]

            ]
        )

        await message.answer("Your portfolio:", reply_markup=keyboard)
    else:
        await message.answer("Error portfolio getting.")


@tg_router.callback_query(F.data == "delete_menu")
async def show_delete_menu(callback: types.CallbackQuery):
    response = requests.get(f"{API_URL}", params={"telegram_id": str(callback.from_user.id)})

    if response.status_code == 200:
        data = response.json()
        coins = [coin.get("symbol") for coin in data]

        if not coins:
            await callback.message.answer("Your portfolio is empty.")
            return

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                                [InlineKeyboardButton(text=coin, callback_data=f"remove_{coin}")] for coin in coins
                            ] + [[InlineKeyboardButton(text="⬅️ Back", callback_data="cancel_delete")]]
        )

        await callback.message.answer("Select a coin to delete:", reply_markup=keyboard)
    else:
        await callback.message.answer("Error retrieving portfolio.")


@tg_router.message(Command("get_report_menu"))
@tg_router.callback_query(F.data == "get_report_menu")
async def show_get_report_menu(event: Union[types.Message, types.CallbackQuery]):
    user_id = event.from_user.id  # Works for both Message & CallbackQuery

    response = requests.get(f"{API_URL}", params={"telegram_id": str(user_id)})

    if response.status_code == 200:
        data = response.json()
        coins = [coin.get("symbol") for coin in data]

        if not coins:
            await event.answer("Your portfolio is empty.") if isinstance(event,
                                                                         types.CallbackQuery) else await event.message.answer(
                "Your portfolio is empty.")
            return

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                                [InlineKeyboardButton(text=coin, callback_data=f"get_report_{coin}")] for coin in coins
                            ] + [[InlineKeyboardButton(text="⬅️ Back", callback_data="cancel_report")]]
        )

        if isinstance(event, types.CallbackQuery):
            await event.message.answer("Select a coin to generate a report:", reply_markup=keyboard)
            await event.answer()  # Acknowledge button press
        else:
            await event.answer("Select a coin to generate a report:", reply_markup=keyboard)

    else:
        await event.answer("Error retrieving portfolio.") if isinstance(event,
                                                                        types.CallbackQuery) else await event.message.answer(
            "Error retrieving portfolio.")


@tg_router.callback_query(F.data == "cancel_delete")
async def cancel_delete(callback: types.CallbackQuery):
    await edit_portfolio_menu(callback.message)


@tg_router.callback_query(F.data == "cancel_report")
async def cancel_report(callback: types.CallbackQuery):
    await edit_portfolio_menu(callback.message)


@tg_router.callback_query(F.data.startswith("remove_"))
async def remove_coin(callback: types.CallbackQuery):
    coin = callback.data.split("_")[1]
    response = requests.delete(f"{API_URL}", params={"telegram_id": str(callback.from_user.id), "symbol": coin})

    if response.status_code == 202:
        await callback.answer(f"✅ Coin **{coin}** removed!", parse_mode='Markdown')
        await edit_portfolio_menu(callback.message)
    else:
        await callback.answer("❌ Error removing coin. Please try again.")


@tg_router.callback_query(F.data == "add_coin")
async def ask_new_coins(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(PortfolioState.choosing_coin)
    await callback.message.answer("Enter new coins (for example, BTC ETH SOL):")
    await callback.answer()


@tg_router.callback_query(F.data.startswith("get_report_"))
async def get_report(callback: types.CallbackQuery):
    coin = callback.data.split("_")[2]

    # ✅ Immediately acknowledge the callback query to prevent timeout
    await callback.answer("📊 Generating report, please wait...", show_alert=False)

    # Fetch chart image
    response = requests.get(f"{API_URL}/selected/chart", params={"symbol": coin})
    if response.status_code == 200:
        image_path = "chart.png"
        with open(image_path, "wb") as f:
            f.write(response.content)

        # ✅ Send the chart image
        await bot.send_photo(chat_id=callback.from_user.id, photo=FSInputFile(image_path),
                             caption="📊 **Crypto Price** vs **Sentiment Analysis**", parse_mode='Markdown')

        # Remove image after sending
        os.remove(image_path)
    else:
        await callback.message.answer("❌ Failed to generate the chart. Try again later.")
        return

    # Fetch additional data (News & Price)
    response = requests.get(f"{API_URL}/selected", params={"symbol": coin})
    if response.status_code == 200:
        data = response.json()
        news = data.get("related_news", "No news available.")
        sentiment_score = data.get("sentiment_score", "No sentiment score")
        price = data.get("current_price", {}).get("price_usd", "N/A")

        # ✅ Send news & price separately
        await callback.message.answer(f"📰 {news}", parse_mode='Markdown')
        await callback.message.answer(f"💰 **Current price:** {price} USD", parse_mode='Markdown')
        try:
            await callback.message.answer(f"💰 **Sentiment_score:** {sentiment_score}", parse_mode='Markdown')
        except TelegramBadRequest as e:
            print(sentiment_score)
            logging.critical(f"Can't parse score! {e}")
        await callback.message.answer("Maybe I can help you more?")
        await edit_portfolio_menu(callback.message)
    else:
        await callback.message.answer(f"❌ Error getting report for {coin}. Please try again.")


@tg_router.callback_query(F.data.startswith("get_total_report"))
async def get_report(callback: types.CallbackQuery):
    user_id = callback.from_user.id  # Works for both Message & CallbackQuery
    response = requests.get(f"{API_URL}", params={"telegram_id": str(user_id)})
    coins = []

    if response.status_code == 200:
        data = response.json()
        coins = [coin.get("symbol") for coin in data]
    for coin in coins:
        # ✅ Immediately acknowledge the callback query to prevent timeout
        await callback.answer(f"📊 Generating report for {coin}, please wait...", show_alert=False)
        # Fetch chart image
        response = requests.get(f"{API_URL}/selected/chart", params={"symbol": coin})
        if response.status_code == 200:
            image_path = "chart.png"
            with open(image_path, "wb") as f:
                f.write(response.content)

            # ✅ Send the chart image
            await bot.send_photo(chat_id=callback.from_user.id, photo=FSInputFile(image_path),
                                 caption=f"📊 **Crypto Price** vs **Sentiment Analysis** for {coin}",
                                 parse_mode='Markdown')

            # Remove image after sending
            os.remove(image_path)
        else:
            await callback.message.answer("❌ Failed to generate the chart. Try again later.")
            return

        # Fetch additional data (News & Price)
        response = requests.get(f"{API_URL}/selected",
                                params={"telegram_id": str(callback.from_user.id), "symbol": coin})
        if response.status_code == 200:
            data = response.json()
            news = data.get("related_news", "No news available.")
            price = data.get("current_price", {}).get("price_usd", "N/A")

            # ✅ Send news & price separately
            await callback.message.answer(f"📰 **News by {coin}:**\n{news}", parse_mode='Markdown')
            await callback.message.answer(f"💰 **Current price of {coin}:** {price} USD", parse_mode='Markdown')
        else:
            await callback.message.answer(f"❌ Error getting report for {coin}. Please try again.")
    await callback.message.answer("Maybe I can help you more?")
    await edit_portfolio_menu(callback.message)


# @tg_router.message(F.text)
# async def process_choice(message: types.Message, state: FSMContext):
#     await state.clear()
#     data = await state.get_data()
#     chosen_token = message.text
#
#     print(f"[DEBUG] User selected: {chosen_token}")
#
#     await state.update_data(token=chosen_token)
#
#     keyboard = types.ReplyKeyboardMarkup(
#         keyboard=[
#             [types.KeyboardButton(text="1"), types.KeyboardButton(text="7"), types.KeyboardButton(text="30")]
#         ],
#         resize_keyboard=True,
#         one_time_keyboard=True
#     )
#
#     await message.answer("Оберіть періодичність оновлення (в днях):", reply_markup=keyboard)
#     await state.set_state(NewsSubscription.choosing_frequency)
#
#
# @tg_router.message(NewsSubscription.choosing_frequency)
# async def process_frequency(message: types.Message, state: FSMContext):
#     frequency = message.text
#     if not frequency.isdigit():
#         await message.answer("Будь ласка, введіть число (кількість днів).")
#         return
#
#     data = await state.get_data()
#     chosen_token = data.get("token")
#
#     print(f"[DEBUG] User subscribed to {chosen_token} with frequency {frequency} days")
#
#     await message.answer(f"Ви підписалися на новини про {chosen_token} раз на {frequency} днів.")
#     await state.clear()


if __name__ == "__main__":
    dp.run_polling(bot)
