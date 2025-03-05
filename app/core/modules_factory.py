from langchain_openai import ChatOpenAI
from redis.asyncio import Redis
from openai import OpenAI

from app.core.config import config, cmc_config, tg_conf, twitter_settings, perplexity_config, elfa_config
from utils import telegram_bot
from utils.twitter_driver import TwitterDriver
from utils.cmc_driver import CoinMarketCapDriver
from utils.perplexity_driver import PerplexityDriver
from utils.elfa_driver import ElfaDriver

# -------- Initialize OpenAI --------------------
MODEL_NAME = "gpt-4o-mini"
LLM_OPEN_AI = ChatOpenAI(
    model_name=MODEL_NAME,
    api_key=config.OPENAI_API_KEY,
    temperature=0
)

# -------- Initialize Telegram Bot --------------------
tg_bot = telegram_bot.TelegramBot(
    token=tg_conf.TG_TOKEN
)

# -------- Initialize Twitter Driver -----------------
twitter_driver = TwitterDriver(
    bearer_token=twitter_settings.BEARER_TOKEN,
    api_key=twitter_settings.API_KEY,
    api_secret=twitter_settings.API_SECRET,
    access_token=twitter_settings.ACCESS_TOKEN,
    access_secret=twitter_settings.ACCESS_SECRET
)

# -------- Initialize CoinMarketCap Driver -----------------
cmc_driver = CoinMarketCapDriver(
    base_url=cmc_config.CMC_URL,
    api_key=cmc_config.CMC_API_KEY
)

# -------- Initialize Perplexity Driver -----------------
perplexity_driver = PerplexityDriver(
    base_url=perplexity_config.PERPLEXITY_URL,
    api_key=perplexity_config.PERPLEXITY_API_KEY
)

# -------- Initialize Elfa Driver -----------------
elfa_driver = ElfaDriver(
    base_url=elfa_config.ELFA_URL,
    api_key=elfa_config.ELFA_API_KEY
)
