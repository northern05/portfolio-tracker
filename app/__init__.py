import logging
import traceback

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exception_handlers import http_exception_handler
from fastapi_limiter import FastAPILimiter
from apscheduler.schedulers.background import BackgroundScheduler

from app.core.models import db_helper, Base
from app.api import router as router_v1
from app.core.config import config, redis_config
from app.core.modules_factory import tg_bot
from utils.general import check_users_retwitt, sell_tokens, log_agent_balance


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_users_retwitt, "cron", minute='*/15')
    scheduler.add_job(sell_tokens, "cron", minute='*/59')
    scheduler.add_job(log_agent_balance, "cron", minute='*/5')
    scheduler.start()

    print("Started lifespan")
    async with db_helper.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield
    print("End lifespan")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router=router_v1, prefix=config.api_v1_prefix)


@app.exception_handler(HTTPException)
async def exception_handler(request: Request, exc: HTTPException):
    logger.info("Handling http exception")
    msg = (await format_request(request)) + "\n\n" + str(exc)

    # await tg_bot.send_message(msg)
    return await http_exception_handler(request, exc)


@app.exception_handler(Exception)
async def exception_handler_2(request: Request, exc: Exception):
    msg = f"URL: {request.url}\n\n"
    msg += traceback.format_exc()

    # await tg_bot.send_message(msg)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content="Server error!"
    )


async def format_request(request: Request):
    msg = f"URL: {request.url}\n"

    body = await request.body()
    msg += f"Body: {body.decode()}"

    return msg


logger = logging.getLogger()
logger.setLevel(logging.INFO)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# add formatter to handlers
if len(logger.handlers) > 0:
    logger.handlers[0].setLevel(logging.DEBUG)
    logger.handlers[0].setFormatter(formatter)
else:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


