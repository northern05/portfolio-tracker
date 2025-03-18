from sqlalchemy import String, ForeignKey, Integer, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .user import User
from .portfolio import Portfolio


class PortfolioUser(Base):
    __tablename__ = "portfolio_users"
    telegram_id: Mapped[str] = mapped_column(String, nullable=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey('portfolios.id'), nullable=False)
    portfolio: Mapped["Portfolio"] = relationship(backref="portfolio_users")