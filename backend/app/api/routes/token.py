from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users import models
from fastapi_users.authentication import Strategy
from fastapi_users.manager import BaseUserManager
from fastapi_users.router import ErrorCode
from starlette.status import HTTP_400_BAD_REQUEST

from ...services.authentication import fastapi_user as fastapi_user_class
from ...services.authentication import get_user_manager

fastapi_user = fastapi_user_class.init()
router = APIRouter()


@router.post("/token")
async def create_token(
    credentials: OAuth2PasswordRequestForm = Depends(),
    user_manager: BaseUserManager[models.UC, models.UD] = Depends(get_user_manager),
    strategy: Strategy[models.UC, models.UD] = Depends(
        fastapi_user.backends[0].get_strategy
    ),
) -> dict[str, str]:
    user = await user_manager.authenticate(credentials)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=ErrorCode.LOGIN_BAD_CREDENTIALS,
        )
    if not user.is_verified:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=ErrorCode.LOGIN_USER_NOT_VERIFIED,
        )

    token = await strategy.write_token(user)
    return {"access_token": token, "token_type": "bearer"}
