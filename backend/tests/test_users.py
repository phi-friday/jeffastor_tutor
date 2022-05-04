import pytest
from app.core import config
from app.models import user
from app.services.authentication import create_strategy
from fastapi import FastAPI, status
from fastapi_users.authentication import JWTStrategy
from fastapi_users.jwt import decode_jwt
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel.ext.asyncio.session import AsyncSession

pytestmark = pytest.mark.anyio


class TestUserRoutes:
    api_name = "users:get-allowed-methods"

    async def test_routes_exist(self, app: FastAPI, client: AsyncClient) -> None:
        res = await client.options(app.url_path_for(self.api_name))
        assert res.status_code == status.HTTP_204_NO_CONTENT
        assert not res.content
        headers = res.headers
        assert "Allow" in headers
        allowed_methods_str = headers["Allow"]
        allowed_methods = {
            method_str.strip().lower() for method_str in allowed_methods_str.split(",")
        }
        assert len(allowed_methods) > 0
        for method_str in ("post",):
            assert method_str in allowed_methods


class TestUserRegistration:
    api_name = "users:register-new-user"

    async def test_users_can_register_successfully(
        self, app: FastAPI, client: AsyncClient, engine: AsyncEngine
    ) -> None:
        new_user = {
            "email": "shakira@shakira.io",
            "name": "shakirashakira",
            "password": "chantaje@1",
        }
        # make sure user doesn't exist yet
        async with AsyncSession(engine, autocommit=False) as session:
            is_user = await user.user_model.get_from_email(
                session=session, email=new_user["email"]
            )
        assert is_user is None
        # send post request to create user and ensure it is successful
        res = await client.post(
            app.url_path_for(self.api_name), json={"new_user": new_user}
        )
        assert res.status_code == status.HTTP_201_CREATED
        # ensure that the user now exists in the db
        async with AsyncSession(engine, autocommit=False) as session:
            is_user = await user.user_model.get_from_email(
                session=session, email=new_user["email"]
            )
        assert is_user is not None
        assert is_user.email == new_user["email"]
        assert is_user.name == new_user["name"]
        # check that the user returned in the response is equal to the user in the database
        created_user = user.user_model.validate(
            res.json() | {"hashed_password": "whatever"}
        )
        exclude_attr_set = user.user_model.datetime_attrs | {"id", "hashed_password"}
        assert created_user.dict(exclude=exclude_attr_set) == is_user.dict(
            exclude=exclude_attr_set
        )

    @pytest.mark.parametrize(
        "attr, value, status_code",
        (
            ("email", "shakira@shakira.io", 400),
            ("name", "sha", 422),
            ("name", "shafasdfsdwerewfsdfxcvxcvxcv", 422),
            ("email", "invalid_email@one@two.io", 422),
            ("password", "short", 422),
            (
                "password",
                (
                    "longlonglonglonglonglonglonglonglonglonglonglong"
                    "longlonglonglonglonglonglonglonglonglonglonglong"
                    "longlonglonglonglonglonglonglonglonglonglonglong"
                ),
                422,
            ),
            ("password", "pattern@", 422),
            ("name", "shakira@#$%^<>", 422),
            ("name", "ab", 422),
        ),
    )
    async def test_user_registration_fails_when_credentials_are_taken(
        self,
        app: FastAPI,
        client: AsyncClient,
        attr: str,
        value: str,
        status_code: int,
    ) -> None:
        new_user = {
            "email": "nottaken@email.io",
            "name": "not_taken_username",
            "password": "freepassword@1",
        }
        new_user[attr] = value
        res = await client.post(
            app.url_path_for(self.api_name), json={"new_user": new_user}
        )
        assert res.status_code == status_code


@pytest.fixture
def strategy() -> JWTStrategy:
    return create_strategy()  # type: ignore


class TestAuthTokens:
    api_name = "users:create-token"

    async def test_can_create_access_token_successfully(
        self,
        app: FastAPI,
        client: AsyncClient,
        test_user: user.user_model,
        strategy: JWTStrategy,
        engine: AsyncEngine,
    ) -> None:
        access_token = await strategy.write_token(user=test_user)
        creds = decode_jwt(
            access_token,
            str(config.SECRET_KEY),
            [config.JWT_AUDIENCE],
            [config.JWT_ALGORITHM],
        )

        assert creds.get("user_id") is not None
        user_id = creds["user_id"]
        assert config.JWT_AUDIENCE in creds["aud"]

        async with AsyncSession(engine, autocommit=False) as session:
            user_model = await session.get(user.user_model, user_id)
        assert user_model is not None

        assert user_model.name == test_user.name

    async def test_token_missing_user_is_invalid(
        self, app: FastAPI, client: AsyncClient
    ) -> None:
        res = await client.post(
            url=app.url_path_for(self.api_name),
            data={"username": "unknown", "password": "testpassword@1"},
        )
        assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
