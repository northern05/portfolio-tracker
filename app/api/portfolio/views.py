import logging
from fastapi import APIRouter, status, Depends

from . import dependencies, schemas

router = APIRouter(tags=["Portfolio"])

logger = logging.getLogger('portfolio/views')


@router.get(
    "/similar_assets",
    status_code=status.HTTP_200_OK,
    response_model=list[schemas.SimilarAssetsResponse],
)
async def get_similar_assets(
        result: list[schemas.SimilarAssetsResponse] = Depends(dependencies.get_similar_assets)
):
    """
    Endpoint to get similar assets
    :return: similar_assets
    """
    return result


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=list[schemas.PortfolioResponse],
)
async def get_all_messages_count(
        result: list[schemas.PortfolioResponse] = Depends(dependencies.get_all_portfolio)
):
    """
    Endpoint to get portfolio over user
    :param session: session to connect to database
    :return: list portfolio
    """
    return result


@router.post(
    "",
    status_code=status.HTTP_200_OK,
    response_model=schemas.PortfolioResponse,
)
async def create_portfolio(
        result: schemas.PortfolioResponse = Depends(dependencies.create_portfolio)
):
    """
    Endpoint to get portfolio over user
    :param session: session to connect to database
    :return: list portfolio
    """
    return result


@router.post(
    "/connect_telegram",
    status_code=status.HTTP_200_OK,
    response_model=schemas.PortfolioResponse,
)
async def connect_tg(
        result: schemas.PortfolioResponse = Depends(dependencies.connect_tg)
):
    """
    Endpoint to get portfolio over user
    :return: list portfolio
    """
    return result


@router.get(
    "/{portfolio_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.PortfolioResponseExtended,
)
async def get_selected_portfolio(
        result: schemas.PortfolioResponseExtended = Depends(dependencies.get_selected_portfolio)
):
    """
    Endpoint to get selected portfolio over user
    :param portfolio_id: portfolio id
    :return: portfolio extended schema
    """
    return result


@router.delete(
    "/{portfolio_id}",
    status_code=status.HTTP_202_ACCEPTED
)
async def delete_portfolio(
        result: schemas.PortfolioResponseExtended = Depends(dependencies.delete_portfolio)
):
    """
    Endpoint to get selected portfolio over user
    :return: portfolio extended schema
    """
