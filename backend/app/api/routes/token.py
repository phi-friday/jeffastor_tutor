from fastapi import APIRouter

from ...dependencies.auth import fastapi_user

router = APIRouter()

# name: auth:{backend.name}.login
router.include_router(
    fastapi_user.users.get_auth_router(
        fastapi_user.backends[0], requires_verification=False
    )
)

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
