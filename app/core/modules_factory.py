from langchain_openai import ChatOpenAI
from redis.asyncio import Redis
from openai import OpenAI

from app.core.config import config, redis_config, tg_conf, twitter_settings, solana_settings
from utils import telegram_bot
from utils.solana_driver import SolanaDriver
from utils.twitter_driver import TwitterDriver

# -------- Initialize REDIS connection --------------------
redis_db = Redis(
    host=redis_config.REDIS_HOST,
    port=redis_config.REDIS_PORT,
    username=redis_config.REDIS_USER,
    password=redis_config.REDIS_PASSWORD,
)

# -------- Initialize OpenAI --------------------
MODEL_NAME = "gpt-4o-mini"
LLM_OPEN_AI = ChatOpenAI(model_name=MODEL_NAME, api_key=config.OPENAI_API_KEY, temperature=0)

# -------- Initialize Telegram Bot --------------------
tg_bot = telegram_bot.TelegramBot(token=tg_conf.TG_TOKEN)

# -------- Initialize Twitter Driver -----------------
twitter_driver = TwitterDriver(bearer_token=twitter_settings.BEARER_TOKEN,
                               api_key=twitter_settings.API_KEY,
                               api_secret=twitter_settings.API_SECRET,
                               access_token=twitter_settings.ACCESS_TOKEN,
                               access_secret=twitter_settings.ACCESS_SECRET
                               )

# -------- Initialize Solana Driver -----------------
solana_driver = SolanaDriver(rpc_url=solana_settings.RPC_URL,
                             config_path=solana_settings.SOLANA_CONFIG_PATH,
                             agent_keypair=solana_settings.AGENT_KEYPAIR,
                             )