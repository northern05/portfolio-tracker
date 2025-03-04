from sqlalchemy import String, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .user import User


class Portfolio(Base):
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    user: Mapped["User"] = relationship(backref="credits")
    symbol = mapped_column(String, nullable=False, index=True)
    name = mapped_column(String, nullable=False, index=True)
    token_address: Mapped[str] = mapped_column(String, nullable=False)

    def __repr__(self):
        return f"<Credits for user{self.user_id}>"
