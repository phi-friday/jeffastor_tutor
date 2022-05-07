from typing import Generic, TypeVar

from fastapi_users import BaseUserManager, FastAPIUsers
from fastapi_users.authentication import AuthenticationBackend, JWTStrategy, Strategy
from fastapi_users.db import SQLAlchemyUserDatabase

from ...models import user
from ...models.core import base_model

user_id_type = user.user_id_type
_T = TypeVar("_T", bound=base_model)
_D = TypeVar("_D")

# fmt: off
class user_db_class(SQLAlchemyUserDatabase[_T, _D], Generic[_T, _D]): ... # type: ignore
class strategy_class(Strategy[_T, _D], Generic[_T, _D]): ... # type: ignore
class jwt_strategy_class(JWTStrategy[_T, _D], Generic[_T, _D]): ... # type: ignore
class auth_backend_class(AuthenticationBackend[_T, _D], Generic[_T, _D]): ... # type: ignore
class user_manager_class(BaseUserManager[_T, _D], Generic[_T, _D]): ...  # type: ignore
class fastapi_users_class(FastAPIUsers[_T, _D], Generic[_T, _D]): ...  # type: ignore
# fmt: on


user_manager_type = user_manager_class[user.user, user_id_type]
strategy_type = strategy_class[user.user, user_id_type]
