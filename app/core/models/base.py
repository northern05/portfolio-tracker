from enum import Enum

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr


class Base(DeclarativeBase):
    __abstract__ = True

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return f"{cls.__name__.lower()}s"

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)


class State(Enum):
    active = "active"
    deleted = "deleted"


class ActionParameter(str, Enum):
    transferPrize = "transferPrize"
    swap = "swap"
    shilling = "shilling"


class ConversationStatus(str, Enum):
    approve = "approve",
    approve_failed = "approve_failed",
    decline = "decline",
    reject = "reject"
    discuss = "discuss"
    ready_to_shilling = "ready_to_shilling"
