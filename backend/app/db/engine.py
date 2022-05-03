from typing import Any, Literal, overload

from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.future.engine import Engine
from sqlalchemy.pool import NullPool, QueuePool

from ..core import config


def get_test_url(url: URL) -> URL:
    if url.database is None:
        raise ValueError("database name is None")

    return url.set(database=f"{url.database}_test")


def get_engine_kwargs(**kwargs: Any) -> dict[str, Any]:
    params: dict[str, Any] = {"pool_pre_ping": True, "future": True}

    if config.TESTING:
        params["poolclass"] = NullPool
    else:
        params["pool_size"] = 10
        params["poolclass"] = QueuePool

    return params | kwargs


@overload
def get_test_engine(engine: AsyncEngine) -> AsyncEngine:
    ...


@overload
def get_test_engine(engine: AsyncEngine, is_sync: Literal[True] = ...) -> Engine:
    ...


@overload
def get_test_engine(engine: AsyncEngine, is_sync: Literal[False] = ...) -> AsyncEngine:
    ...


@overload
def get_test_engine(engine: AsyncEngine, is_sync: bool = ...) -> AsyncEngine | Engine:
    ...


def get_test_engine(engine: AsyncEngine, is_sync: bool = False) -> AsyncEngine | Engine:
    if config.TESTING:
        engine = create_engine_from_url(get_test_url(engine.url))

    if is_sync:
        return convert_async_to_sync(engine)
    return engine


def convert_async_to_sync(engine: AsyncEngine, **kwargs: Any) -> Engine:
    return create_sync_engine_from_url(
        engine.url.set(drivername=engine.url.drivername.split("+")[0]), **kwargs
    )


def create_sync_engine_from_url(url: str | URL, **kwargs: Any) -> Engine:
    return create_engine(url, **get_engine_kwargs(**kwargs))


def create_engine_from_url(url: str | URL, **kwargs: Any) -> AsyncEngine:
    return create_async_engine(url, **get_engine_kwargs(**kwargs))


engine = create_engine_from_url(config.DATABASE_URL)
