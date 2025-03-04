from contextlib import asynccontextmanager


@asynccontextmanager
async def get_db_session():
    """
    Wraps the async generator returned by db_helper.scoped_session_dependency()
    so that it can be used with an `async with` statement.
    """
    from app.core.models.db_helper import db_helper
    session_gen = db_helper.scoped_session_dependency()
    try:
        session = await anext(session_gen)
    except StopAsyncIteration:
        raise ValueError("No session yielded by the async generator.")
    try:
        yield session
    finally:
        await session_gen.aclose()
