from datetime import datetime
from typing import Generic

from fastapi import Request
from fastapi_users import models
from fastapi_users.authentication.strategy import JWTStrategy
from fastapi_users.exceptions import FastAPIUsersException, InvalidID, UserNotExists
from fastapi_users.jwt import decode_jwt, generate_jwt
from fastapi_users.manager import BaseUserManager

from jwt import ExpiredSignatureError, PyJWTError


class invalid_request(FastAPIUsersException):
    ...


class diff_origin(invalid_request):
    ...


class expire_refresh(invalid_request):
    ...


class request_jwt_strategy(
    JWTStrategy[models.UP, models.ID], Generic[models.UP, models.ID]
):
    origin_key = "request_origin"
    user_key = "user_id"

    async def read_token(
        self,
        request: Request | None,
        token: str | None,
        user_manager: BaseUserManager[models.UP, models.ID],
    ) -> models.UP | None:
        if request is None or token is None:
            return None

        try:
            data = decode_jwt(
                token, self.decode_key, self.token_audience, algorithms=[self.algorithm]
            )
        except ExpiredSignatureError:
            ...
        except PyJWTError:
            return None

        origin = data.get(self.origin_key)
        if origin is None:
            return None
        elif origin != [request.client.host, request.client.port]:
            raise diff_origin()

        user_id = data.get(self.user_key)
        if user_id is None:
            return None

        try:
            parsed_id = user_manager.parse_id(user_id)
            return await user_manager.get(parsed_id)
        except (exceptions.UserNotExists, exceptions.InvalidID):
            return None

    async def write_token(self, user: models.UP) -> str:
        return await super().write_token(user)
