from typing import AsyncIterator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio.engine import AsyncEngine
from sqlmodel.ext.asyncio.session import AsyncSession


async def get_database(request: Request) -> AsyncEngine:
    if (engine := getattr(request.app.state, "_db", None)) is None:
        raise AttributeError("there is no database engine in request as state")
    return engine


async def get_session(
    engine: AsyncEngine = Depends(get_database),
) -> AsyncIterator[AsyncSession]:
    async with AsyncSession(engine, autoflush=False, autocommit=False) as session:
        yield session
