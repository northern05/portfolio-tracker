import os

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    api_v1_prefix: str = "/portfolio_tracker/api/v1"
    APP_DOMAIN: str = "api.agent.zpoken.dev"


class RedisSettings(BaseSettings):
    REDIS_HOST: str = os.environ.get('REDIS_HOST')
    REDIS_PORT: str = os.environ.get('REDIS_PORT')
    REDIS_USER: str = os.environ.get('REDIS_USER')
    REDIS_PASSWORD: str = os.environ.get('REDIS_PASSWORD')
    REDIS_URL: str = f"redis://{REDIS_USER}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}"


class DBSettings(BaseSettings):
    DB_NAME: str = os.environ.get("DB_NAME")
    DB_USER: str = os.environ.get("DB_USER")
    DB_HOST: str = os.environ.get("DB_HOST")
    DB_PORT: str = os.environ.get("DB_PORT")
    DB_PW: str = os.environ.get("DB_PW")

    SQLALCHEMY_DATABASE_URL: str = (
        f"postgresql+asyncpg://{DB_USER}:{DB_PW}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    db_echo: bool = False


class CoinMarketCapSettings(BaseSettings):
    CMC_URL: str = os.environ.get("CMC_URL", "https://pro-api.coinmarketcap.com/v1/cryptocurrency")
    CMC_API_KEY: str = os.environ.get("CMC_API_KEY")


class ElfaSettings(BaseSettings):
    ELFA_URL: str = os.environ.get("CMC_URL", "https://api.elfa.ai/v1")
    ELFA_API_KEY: str = os.environ.get("ELFA_API_KEY")


class PerplexitySettings(BaseSettings):
    PERPLEXITY_URL: str = os.environ.get("PERPLEXITY_URL", "https://api.perplexity.ai")
    PERPLEXITY_API_KEY: str = os.environ.get("PERPLEXITY_API_KEY")


class TwitterCredentialsSettings(BaseSettings):
    accounts: str = os.environ.get("TWITTER_ACCOUNTS")
    ACCOUNTS: list = json.loads(accounts)


class LLamaSettings(BaseSettings):
    LLAMA_URL: str = os.environ.get("LLAMA_URL", "http://195.189.60.154:8000/generate")


config = Config()
db_config = DBSettings()
cmc_config = CoinMarketCapSettings()
elfa_config = ElfaSettings()
perplexity_config = PerplexitySettings()
redis_config = RedisSettings()
llama_config = LLamaSettings()
twitter_account_config = TwitterCredentialsSettings()
