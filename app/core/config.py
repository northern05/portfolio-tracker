import os

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    api_v1_prefix: str = "/portfolio_tracker/api/v1"
    APP_DOMAIN: str = "api.agent.zpoken.dev"


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


class TelegramSettings(BaseSettings):
    TG_TOKEN: str = os.environ.get('TG_TOKEN', "7540334723:AAFGudo28Myy4ltPmZLz3jhODPY4iVrkRG4")
    BASE_SITE: str = os.environ.get('BASE_SITE', "https://api.agent.zpoken.dev/portfolio_tracker/api/v1/portfolio")
    API_KEY: str = os.environ.get('TG_API_KEY', "tg_api_key")


class CoinMarketCapSettings(BaseSettings):
    CMC_URL: str = os.environ.get("CMC_URL", "https://pro-api.coinmarketcap.com/v1/cryptocurrency")
    CMC_API_KEY: str = os.environ.get("CMC_API_KEY")


class ElfaSettings(BaseSettings):
    ELFA_URL: str = os.environ.get("CMC_URL", "https://api.elfa.ai/v1")
    ELFA_API_KEY: str = os.environ.get("ELFA_API_KEY")


class PerplexitySettings(BaseSettings):
    PERPLEXITY_URL: str = os.environ.get("PERPLEXITY_URL", "https://api.perplexity.ai")
    PERPLEXITY_API_KEY: str = os.environ.get("ELFA_API_KEY")


config = Config()
db_config = DBSettings()
cmc_config = CoinMarketCapSettings()
elfa_config = ElfaSettings()
perplexity_config = PerplexitySettings()
tg_conf = TelegramSettings()
