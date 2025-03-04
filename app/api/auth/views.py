import pickle
import logging
from fastapi import APIRouter, Body, Cookie, HTTPException, Response, status, Depends, Request
from fastapi.responses import PlainTextResponse
from siwe import generate_nonce, SiweMessage

from app.core.modules_factory import redis_db
from utils.general import generate_session_id
from app.core.models import User

from . import dependencies
from ...core.config import COOKIE_SESSION_ID_KEY

logger = logging.getLogger("auth/views")

router = APIRouter(
    tags=["Authorization"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/nonce",
    response_class=PlainTextResponse
)
async def get_nonce(
        response: Response,
        request: Request,
        session_id: str = Cookie(alias=COOKIE_SESSION_ID_KEY, default=None),
):
    """
    Endpoint that returns nonce based on session, wallet users cookies
    :param response: response to front with cookies
    :param request: request to back-end
    :param session_id: users session id from cookies
    :return: nonce
    """
    logger.info('Received /nonce')
    logger.debug("IP: %s", request.client.host)
    logger.debug("Platform: %s", request.headers.get("sec-ch-ua-platform"))
    logger.debug("Browser: %s", request.headers.get("sec-ch-ua"))

    # do not generate new session id if current session id is valid
    if session_id:
        sesion_info_str = redis_db.get(session_id)
        if sesion_info_str:
            session_info = pickle.loads(sesion_info_str)
            if session_info.get('siwe'):
                return session_info.get("nonce")

    try:
        session_id = generate_session_id()

        nonce = generate_nonce()
        session_info = {
            'nonce': nonce
        }
        redis_db.set(session_id, pickle.dumps(session_info))

        response.set_cookie(
            key=COOKIE_SESSION_ID_KEY,
            value=session_id)

        logger.debug("Return nonce %s. Session id: %s", nonce, session_id)

        return nonce
    except Exception as e:
        logger.error(e)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate nonce"
        )


@router.post('/verify')
def verify(
        message: str = Body(),
        signature: str = Body(),
        session_id: str = Cookie(alias=COOKIE_SESSION_ID_KEY)
):
    """
    Endpoint to verify nonce
    :param message: message from siwe
    :param signature: signature to verify siwe
    :param session_id: users session id from cookies
    :return: True if verified
    """
    logger.info("Got verify. Session id: %s", session_id)
    try:
        siwe_message = SiweMessage.from_message(message)

        session_info = pickle.loads(redis_db.get(session_id))
        siwe_message.verify(
            signature=signature,
            nonce=session_info['nonce']
        )

        session_info['siwe'] = siwe_message
        redis_db.set(session_id, pickle.dumps(session_info))
        # COOKIES[session_id]['expires'] = int(time.time())

        logger.debug("Verified successfully. Session id: %s", session_id)

        return True
    except:
        logger.exception("Failed to verify. Session id: %s", session_id)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Wrong credentials {session_id}",
        )


@router.post("/logout")
async def logout(
        session_id: str = Cookie(alias=COOKIE_SESSION_ID_KEY)
):
    """
    Endpoint to logout users
    :param session_id: users session id from cookies
    :return: None
    """
    logger.info("Received logout. Session id: %s", session_id)
    try:
        redis_db.delete(session_id)

        logger.debug("Successfully logged out. Session id: %s", session_id)
    except Exception:
        logger.exception("Failed to logout. Session id: %s", session_id)


@router.get("/me")
async def me(
        user: User = Depends(dependencies.extract_user_from_access_token),
):
    """
    Endpoint to return user's wallet connected
    :param user: user extracted from access token
    :return: user's wallet
    """
    logger.info("Gout /me. Wallet %s", user.wallet)
    return user.wallet
