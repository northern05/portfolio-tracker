from pydantic import BaseModel, ConfigDict


class PortfolioBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    period_days: int | None = None
    telegram_id: str | None = None


class PortfolioCreate(BaseModel):
    telegram_id: str
    symbol: str


class PortfolioUpdate(PortfolioBase):
    pass


class PortfolioResponse(PortfolioBase):
    pass


class PortfolioResponseExtended(PortfolioBase):
    related_news: str | None = None
    current_price: dict | None = None


class ConnectTelegram(BaseModel):
    telegram_id: str
    wallet: str


class SimilarAssetsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    symbol: str
    name: str
    image_url: str
