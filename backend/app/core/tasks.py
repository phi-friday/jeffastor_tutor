from typing import Any, Callable, Coroutine

from fastapi import FastAPI

from ..db.tasks import close_db_connection, connect_to_db


def create_start_app_handler(app: FastAPI) -> Callable[[], Coroutine[Any, Any, None]]:
    async def start_app() -> None:
        await connect_to_db(app)

    return start_app


def create_stop_app_handler(app: FastAPI) -> Callable[[], Coroutine[Any, Any, None]]:
    async def stop_app() -> None:
        await close_db_connection(app)

    return stop_app
