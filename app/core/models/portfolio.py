from sqlalchemy import String, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .user import User


class Portfolio(Base):
    symbol = mapped_column(String, nullable=False, index=True)
    period_days: Mapped[int] = mapped_column(Integer, nullable=False)

    def __repr__(self):
        return f"<Portfolio for user {self.user_id}, by asset {self.symbol}, with period {self.period}>"
