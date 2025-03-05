from sqlalchemy import String, ForeignKey, Integer, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .user import User
from .portfolio import Portfolio


class PortfolioUser(Base):
    __tablename__ = "portfolio_users"
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    user: Mapped["User"] = relationship(backref="portfolio_users")
    portfolio_id: Mapped[int] = mapped_column(ForeignKey('portfolios.id'), nullable=False)
    portfolio: Mapped["Portfolio"] = relationship(backref="portfolio_users")