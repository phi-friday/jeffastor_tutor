import os
import warnings
from typing import AsyncIterator

import alembic
import pytest
from alembic.config import Config
from app.db.session import async_session
from app.models import user
from app.services.authentication import UserManager, create_strategy
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users.manager import UserNotExists
from httpx import AsyncClient
from sqlalchemy.ext.asyncio.engine import AsyncEngine


@pytest.fixture(
    params=[pytest.param(("asyncio", {"use_uvloop": True}), id="asyncio+uvloop")]
)
def anyio_backend(request):
    return request.param


# Apply migrations at beginning and end of testing session
@pytest.fixture(scope="session")
def apply_migrations():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    os.environ["TESTING"] = "1"
    config = Config("alembic.ini")

    alembic.command.upgrade(config, "head")  # type: ignore
    yield
    alembic.command.downgrade(config, "base")  # type: ignore


# Create a new application for testing
@pytest.fixture
def app(apply_migrations: None) -> FastAPI:
    from app.api.server import get_application

    return get_application()


# Grab a reference to our database when needed
@pytest.fixture
def engine(app: FastAPI) -> AsyncEngine:
    return app.state._db


@pytest.fixture
async def test_user(engine: AsyncEngine) -> user.user:
    new_user = user.user_create.parse_obj(
        dict(
            email="lebron@james.io",
            name="lebronjames",
            password="heatcavslakers@1",
        )
    )

    async with async_session(engine, autocommit=False) as session:
        db = SQLAlchemyUserDatabase(user.user, session, user.user)  # type: ignore
        manager = UserManager(db)

        try:
            new_user_db = await manager.get_by_email(new_user.email)
        except UserNotExists:
            new_user_db = await manager.create(new_user, safe=True)

    return new_user_db


# Make requests in our tests
@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with LifespanManager(app):
        async with AsyncClient(
            app=app,
            base_url="http://testserver",
            headers={"Content-Type": "application/json"},
        ) as client:
            yield client


@pytest.fixture
async def authorized_client(client: AsyncClient, test_user: user.user) -> AsyncClient:
    from app.core import config

    strategy = create_strategy()
    access_token = await strategy.write_token(user=test_user)  # type: ignore

    client.headers["Authorization"] = f"{config.JWT_TOKEN_PREFIX} {access_token}"
    return client
