from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Portfolio(Base):
    symbol: Mapped[str] = mapped_column(String, nullable=False, index=True)
    period_days: Mapped[int] = mapped_column(Integer, nullable=True)
    coingecko_id: Mapped[str] = mapped_column(String)
    twitter: Mapped[str] = mapped_column(String)

    def __repr__(self):
        return f"<Portfolio by asset {self.symbol}, with period {self.period_days}>"
