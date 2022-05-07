from fastapi import APIRouter, Response

from ...services.authentication import fastapi_user_class

fastapi_user = fastapi_user_class.init()
router = APIRouter()

# name: auth:{backend.name}.login
# router.include_router(
#     fastapi_user.users.get_auth_router(
#         fastapi_user.backends[0], requires_verification=False
#     )
# )

# from fastapi import Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordRequestForm
# from fastapi_users.router import ErrorCode

# from ...services.authentication import strategy_type, token_model, user_manager_type

# @router.post("", name="users:create-token")
# async def create_token(
#     credentials: OAuth2PasswordRequestForm = Depends(),
#     user_manager: user_manager_type = fastapi_user.user_manager_depends,
#     strategy: strategy_type = fastapi_user.strategy_depends(),
# ) -> token_model:
#     get_user = await user_manager.authenticate(credentials)
#     if get_user is None or not get_user.is_active:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=ErrorCode.LOGIN_BAD_CREDENTIALS,
#         )
#     if not get_user.is_verified:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=ErrorCode.LOGIN_USER_NOT_VERIFIED,
#         )

#     token = await strategy.write_token(get_user)
#     return token_model.from_token(token)

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users.router import ErrorCode

from ...services.authentication import backend_type, strategy_type, user_manager_type


@router.post("", name="users:create-token")
async def create_token(
    response: Response,
    credentials: OAuth2PasswordRequestForm = Depends(),
    user_manager: user_manager_type = fastapi_user.user_manager_depends,
    access_backend: backend_type = fastapi_user.backend_depends("access-token"),
    refresh_backend: backend_type = fastapi_user.backend_depends("refresh-token"),
):
    get_user = await user_manager.authenticate(credentials)
    if get_user is None or not get_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorCode.LOGIN_BAD_CREDENTIALS,
        )
    # if not get_user.is_verified:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail=ErrorCode.LOGIN_USER_NOT_VERIFIED,
    #     )

    access_strategy: strategy_type = access_backend.get_strategy()
    access_token = await access_strategy.write_token(get_user)
    await access_backend.transport.get_login_response(
        token=access_token, response=response
    )
    refresh_strategy: strategy_type = refresh_backend.get_strategy()
    refresh_token = await refresh_strategy.write_token(get_user)
    await refresh_backend.transport.get_login_response(
        token=refresh_token, response=response
    )
