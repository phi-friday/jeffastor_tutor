import logging
from typing import cast

from fastapi import FastAPI
from sqlalchemy.ext.asyncio.engine import AsyncEngine

from .engine import engine, get_test_engine

logger = logging.getLogger(__name__)


async def connect_to_db(app: FastAPI) -> None:
    _engine = get_test_engine(engine)

    try:
        async with _engine.connect():
            logger.info(
                f"connected db: {_engine.url.render_as_string(hide_password=True)}"
            )
        app.state._db = _engine
    except Exception as e:
        logger.warning("--- DB CONNECTION ERROR ---")
        logger.warning(e)
        logger.warning("--- DB CONNECTION ERROR ---")


async def close_db_connection(app: FastAPI) -> None:
    engine = cast(AsyncEngine, app.state._db)
    try:
        await engine.dispose()
    except Exception as e:
        logger.warning("--- DB DISCONNECT ERROR ---")
        logger.warning(e)
        logger.warning("--- DB DISCONNECT ERROR ---")
