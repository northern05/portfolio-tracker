from pydantic import BaseModel, ConfigDict


class PortfolioBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    period_days: int | None = None
    telegram_id: int | None = None


class PortfolioCreate(BaseModel):
    telegram_id: int
    symbol: str


class PortfolioUpdate(PortfolioBase):
    pass


class PortfolioResponse(PortfolioBase):
    pass


class PortfolioResponseExtended(PortfolioBase):
    sentiment_score: str | None = None
    related_news: list | None = None
    current_price: float | None = None


class ConnectTelegram(BaseModel):
    telegram_id: int
    wallet: str


class SimilarAssetsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    symbol: str
    name: str
    image_url: str
