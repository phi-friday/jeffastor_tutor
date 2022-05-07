import re

import orjson
from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response, status
from fastapi_users.exceptions import InvalidPasswordException, UserAlreadyExists
from pydantic import ValidationError

from ...models import user
from ...services.authentication import fastapi_user_class, user_manager_type

fastapi_user = fastapi_user_class.init()
router = APIRouter()
re_deny_name = re.compile(r"[^a-zA-Z0-9_-]")

get_current_user = fastapi_user.users.current_user(
    optional=False, active=True, verified=False, superuser=False
)


@router.options("", name="users:get-allowed-methods")
async def get_allowed_user_methods() -> Response:
    from functools import reduce

    method_sets = [getattr(route, "methods") for route in router.routes]
    all_methods = reduce(lambda left, right: left | right, method_sets, set())
    all_methods_str = ", ".join(all_methods)

    return Response(
        status_code=status.HTTP_204_NO_CONTENT, headers={"Allow": all_methods_str}
    )


@router.post(
    "",
    name="users:register-new-user",
    response_model=user.user_read,
    status_code=status.HTTP_201_CREATED,
)
async def register_new_user(
    request: Request,
    new_user: user.user_create = Body(..., embed=True),
    user_manager: user_manager_type = fastapi_user.user_manager_depends,
) -> user.user:
    if re_deny_name.search(new_user.name):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "The name can only contain the following characters: "
                f"{re_deny_name.pattern.replace('^','')}"
            ),
        )

    try:
        return await user_manager.create(new_user, safe=True, request=request)
    except UserAlreadyExists as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "That email is already taken. "
                "Login with that email or register with another one."
            ),
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=orjson.loads(exc.json()),
        )
    except InvalidPasswordException as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.reason,
        )


@router.get("/me", response_model=user.user_read, name="users:get-current-user")
async def get_currently_authenticated_user(
    current_user: user.user = Depends(get_current_user),
) -> user.user:
    return current_user
