import os

# import dotenv
from pydantic_settings import BaseSettings

COOKIE_SESSION_ID_KEY: str = os.environ.get("COOKIE_SESSION_ID_KEY", "agent-session-id")

# dotenv.load_dotenv()

class Config(BaseSettings):
    api_v1_prefix: str = "/api/v1"

    APP_DOMAIN: str = "api.agent.zpoken.dev"
    OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY")
    ELFA_API_KEY: str = os.environ.get("ELFA_API_KEY")


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

class SolanaSettings(BaseSettings):
    RPC_URL: str = os.environ.get("RPC_URL")
    SOLANA_CONFIG_PATH: str = os.environ.get("SOLANA_CONFIG_PATH")
    AGENT_KEYPAIR: str = os.environ.get("AGENT_KEYPAIR")

class TwitterSettings(BaseSettings):
    API_KEY: str = os.environ.get("API_KEY")
    API_SECRET: str = os.environ.get("API_SECRET")
    ACCESS_TOKEN: str = os.environ.get("ACCESS_TOKEN")
    ACCESS_SECRET: str = os.environ.get("ACCESS_SECRET")
    BEARER_TOKEN: str = os.environ.get("BEARER_TOKEN")


config = Config()
db_config = DBSettings()
solana_config = SolanaSettings()
twitter_settings = TwitterSettings()
solana_settings = SolanaSettings()
