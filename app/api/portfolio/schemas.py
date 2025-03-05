from enum import Enum

from pydantic import BaseModel, ConfigDict


class PortfolioBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    period_days: int


class PortfolioCreate(PortfolioBase):
    pass


class PortfolioUpdate(PortfolioBase):
    pass


class PortfolioResponse(PortfolioBase):
    pass


class PortfolioResponseExtended(PortfolioBase):
    sentiment_score: str
    related_news: list
    current_price: float


class SimilarAssetsResponse(BaseModel):
    symbol: str
    name: str
    image_url: str
