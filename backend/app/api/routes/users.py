from fastapi import APIRouter

from ...services.authentication import fastapi_user as fastapi_user_class

fastapi_user = fastapi_user_class.init()
router = APIRouter()


router.include_router(
    fastapi_user.users.get_auth_router(fastapi_user.backends[0]), prefix="/auth"
)
router.include_router(fastapi_user.users.get_register_router(), prefix="/auth")
router.include_router(fastapi_user.users.get_verify_router(), prefix="/auth")
