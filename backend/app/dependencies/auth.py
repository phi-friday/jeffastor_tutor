from ..services.authentication import fastapi_user_class

fastapi_user = fastapi_user_class.init()

get_current_user = fastapi_user.users.current_user(
    optional=False, active=True, verified=False, superuser=False
)
get_user_manager = fastapi_user.get_user_manager
get_backend = fastapi_user.get_backend
get_transport = fastapi_user.get_transport
get_strategy = fastapi_user.get_strategy
