import logging

from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from . import dependencies

router = APIRouter(tags=["General"])

logger = logging.getLogger('general/views')


@router.post(
    "/check_retwitts",
    status_code=status.HTTP_200_OK
)
async def _check_retwitts(
        response=Depends(dependencies.check_retwitts)
):
    return response


@router.post(
    "/sell_tokens",
    status_code=status.HTTP_200_OK
)
async def _sell_tokens(
        response=Depends(dependencies.sell_tokens)
):
    return response

@router.post(
    "/log_agent_balance",
    status_code=status.HTTP_200_OK
)
async def _log_agent_balance(
        response=Depends(dependencies.log_agent_balance)
):
    return response



@router.post(
    "/connect_twitter",
    status_code=status.HTTP_200_OK
)
async def _connect_twitter(
        response=Depends(dependencies.connect_twitter)
):
    return response
