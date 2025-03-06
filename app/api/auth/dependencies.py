from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import db_helper, User
from . import crud


async def check_wallet(
        wallet_address: str,
        session: AsyncSession = Depends(db_helper.scoped_session_dependency),
) -> User:
    """
    Method to return user by wallet address
    :param wallet_address: wallet address to check
    :param session: session to connect to database
    :return: user
    """
    user = await crud.select_by_wallet(session=session, wallet=wallet_address)
    if not user:
        user = await crud.add_user(session=session, wallet=wallet_address)
    return user
