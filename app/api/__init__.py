from fastapi import APIRouter

from .auth.views import router as auth_router
from .chats.views import router as chats_router
from .portfolio.views import router as statistics_router
from .general.views import router as general_router

router = APIRouter()

router.include_router(router=auth_router, prefix="/auth")
router.include_router(router=chats_router, prefix="/chats")
router.include_router(router=statistics_router, prefix="/portfolio")
router.include_router(router=general_router, prefix="/general")
