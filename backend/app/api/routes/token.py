from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users.authentication import Strategy
from fastapi_users.manager import BaseUserManager
from fastapi_users.router import ErrorCode

from ...models import user
from ...services.authentication import fastapi_user as fastapi_user_class
from ...services.authentication import get_user_manager

fastapi_user = fastapi_user_class.init()
router = APIRouter()


@router.post("")
async def create_token(
    credentials: OAuth2PasswordRequestForm = Depends(),
    user_manager: BaseUserManager[user.user_create, user.user] = Depends(
        get_user_manager
    ),
    strategy: Strategy[user.user_create, user.user] = Depends(
        fastapi_user.backends[0].get_strategy
    ),
) -> dict[str, str]:
    get_user = await user_manager.authenticate(credentials)
    if get_user is None or not get_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorCode.LOGIN_BAD_CREDENTIALS,
        )
    if not get_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorCode.LOGIN_USER_NOT_VERIFIED,
        )

    token = await strategy.write_token(get_user)
    return {"access_token": token, "token_type": "bearer"}
