import os
import re
import requests
from linkify_it import LinkifyIt
from urllib.parse import urlparse

from aiogram.fsm.state import State, StatesGroup

API_URL: str = os.environ.get('BASE_SITE', "https://api.agent.zpoken.dev/portfolio_tracker/api/v1/portfolio")
self_id = 7540334723
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


class PortfolioState(StatesGroup):
    entering_wallet = State()
    choosing_coin = State()
    enter_coin = State()
    choosing_frequency = State()


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


def escape_markdown(text):
    """
    Escapes special characters for Telegram MarkdownV2 formatting.
    """
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(r'([%s])' % re.escape(escape_chars), r'\\\1', text)


def format_urls_in_report(report):
    linkify = LinkifyIt()
    matches = linkify.match(report)
    if not matches:
        return report

    # Reverse the matches list to replace from the end of the string
    for match in reversed(matches):
        url = match.url
        domain = urlparse(url).netloc
        markdown_link = f'[{domain}]({url})'
        # Replace the URL in the report; match.index and match.last_index give the span of the URL
        report = report[:match.index] + markdown_link + report[match.last_index:]

    return report