import pytest
from app.core import config
from app.db.session import async_session
from app.models import user
from app.services.authentication import (
    UserManager,
    create_strategy,
    jwt_strategy_class,
    user_db_class,
)
from fastapi import FastAPI, status
from fastapi_users.jwt import decode_jwt
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine

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
        async with async_session(engine, autocommit=False) as session:
            is_user = await user.user.get_from_email(
                session=session, email=new_user["email"]
            )
        assert is_user is None
        # send post request to create user and ensure it is successful
        res = await client.post(
            app.url_path_for(self.api_name), json={"new_user": new_user}
        )
        assert res.status_code == status.HTTP_201_CREATED
        # ensure that the user now exists in the db
        async with async_session(engine, autocommit=False) as session:
            is_user = await user.user.get_from_email(
                session=session, email=new_user["email"]
            )
        assert is_user is not None
        assert is_user.email == new_user["email"]
        assert is_user.name == new_user["name"]
        # check that the user returned in the response is equal to the user in the database
        created_user = user.user.validate(res.json() | {"hashed_password": "whatever"})
        exclude_attr_set = user.user.datetime_attrs | {"id", "hashed_password"}
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
def strategy() -> jwt_strategy_class:
    return create_strategy()  # type: ignore


class TestAuthTokens:
    api_name = f"auth:{config.AUTH_BACKEND_NAME}.login"

    async def test_can_create_access_token_successfully(
        self,
        app: FastAPI,
        client: AsyncClient,
        test_user: user.user,
        strategy: jwt_strategy_class,
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
        user_id = user.user.id_type(creds["user_id"])
        assert config.JWT_AUDIENCE in creds["aud"]

        async with async_session(engine, autocommit=False) as session:
            user_model = await session.get(user.user, user_id)
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


class TestUserLogin:
    api_name = f"auth:{config.AUTH_BACKEND_NAME}.login"

    async def test_user_can_login_successfully_and_receives_valid_token(
        self,
        app: FastAPI,
        client: AsyncClient,
        test_user: user.user,
        strategy: jwt_strategy_class,
        engine: AsyncEngine,
    ) -> None:
        client.headers["content-type"] = "application/x-www-form-urlencoded"
        login_data = {"username": test_user.email, "password": "heatcavslakers@1"}
        res = await client.post(app.url_path_for(self.api_name), data=login_data)
        assert res.status_code == status.HTTP_200_OK
        # check that token exists in response and has user encoded within it
        token = res.json().get("access_token")

        async with async_session(engine, autocommit=False) as session:
            db = user_db_class(session, user.user)
            manager = UserManager(db)  # type: ignore

            read_user: user.user | None = await strategy.read_token(token, manager)
        assert read_user is not None
        assert read_user.name == test_user.name
        assert read_user.email == test_user.email
        # check that token is proper type
        assert "token_type" in res.json()
        assert res.json().get("token_type") == "bearer"

    @pytest.mark.parametrize(
        "credential, wrong_value, status_code",
        (
            ("email", "wrong@email.com", 400),
            ("email", None, 422),
            ("email", "notemail", 400),
            ("password", "wrongpassword@1", 400),
            ("password", None, 422),
        ),
    )
    async def test_user_with_wrong_creds_doesnt_receive_token(
        self,
        app: FastAPI,
        client: AsyncClient,
        test_user: user.user,
        credential: str,
        wrong_value: str,
        status_code: int,
    ) -> None:
        client.headers["content-type"] = "application/x-www-form-urlencoded"
        user_data = test_user.dict()
        user_data["password"] = "heatcavslakers@1"
        user_data[credential] = wrong_value
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"],  # insert password from parameters
        }
        res = await client.post(app.url_path_for(self.api_name), data=login_data)
        assert res.status_code == status_code
        assert "access_token" not in res.json()


class TestUserMe:
    api_name = "users:get-current-user"

    async def test_authenticated_user_can_retrieve_own_data(
        self,
        app: FastAPI,
        authorized_client: AsyncClient,
        test_user: user.user,
    ) -> None:
        res = await authorized_client.get(app.url_path_for(self.api_name))
        assert res.status_code == status.HTTP_200_OK
        res_dict: dict = res.json()
        res_dict["hashed_password"] = "testpassword@1"
        read_user = user.user.validate(res_dict)
        assert read_user.email == test_user.email
        assert read_user.name == test_user.name
        assert read_user.id == test_user.id

    async def test_user_cannot_access_own_data_if_not_authenticated(
        self,
        app: FastAPI,
        client: AsyncClient,
        test_user: user.user,
    ) -> None:
        res = await client.get(app.url_path_for("users:get-current-user"))
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        "jwt_prefix",
        (
            ("",),
            ("value",),
            ("Token",),
            ("JWT",),
            ("Swearer",),
        ),
    )
    async def test_user_cannot_access_own_data_with_incorrect_jwt_prefix(
        self,
        app: FastAPI,
        client: AsyncClient,
        test_user: user.user,
        strategy: jwt_strategy_class,
        jwt_prefix: str,
    ) -> None:
        token = await strategy.write_token(test_user)
        res = await client.get(
            app.url_path_for("users:get-current-user"),
            headers={"Authorization": f"{jwt_prefix} {token}"},
        )
        assert res.status_code == status.HTTP_401_UNAUTHORIZED
