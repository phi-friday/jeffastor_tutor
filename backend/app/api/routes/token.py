from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users.router import ErrorCode

from ...services.authentication import fastapi_user as fastapi_user_class
from ...services.authentication import strategy_type, token_model, user_manager_type

fastapi_user = fastapi_user_class.init()
router = APIRouter()


@router.post("")
async def create_token(
    credentials: OAuth2PasswordRequestForm = Depends(),
    user_manager: user_manager_type = fastapi_user.user_manager_depends,
    strategy: strategy_type = fastapi_user.strategy_depends(),
) -> token_model:
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
    return token_model.from_token(token)
