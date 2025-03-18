from pydantic import BaseModel, ConfigDict


class PortfolioBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    period_days: int | None = None
    telegram_id: str | None = None


class PortfolioCreate(BaseModel):
    telegram_id: str
    symbol: str
    twitter: str
    coingecko_id: str


class PortfolioUpdate(PortfolioBase):
    pass


class PortfolioResponse(PortfolioBase):
    pass


class PortfolioResponseExtended(PortfolioBase):
    related_news: str | None = None
    price_movements: str | None = None
    investment_landscape: str | None = None
    current_price: dict | None = None


class SentimentScore(BaseModel):
    sentiment_score: str


class ConnectTelegram(BaseModel):
    telegram_id: str
    wallet: str


class SimilarAssetsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    symbol: str
    name: str
    image_url: str
    market_cap: float
    token_id: str
    twitter: str | None = None
