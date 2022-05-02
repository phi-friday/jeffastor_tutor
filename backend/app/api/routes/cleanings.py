from typing import cast

import orjson
from fastapi import APIRouter, Body, Depends, HTTPException, Path
from pydantic import ValidationError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.status import (
    HTTP_201_CREATED,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from ...db.session import get_session
from ...models.cleaning import (
    cleaning_create,
    cleaning_public,
    cleaning_update,
    cleanings,
)

router = APIRouter()


@router.get(
    "", response_model=list[cleaning_public], name="cleanings:get-all-cleanings"
)
async def get_all_cleanings(
    session: AsyncSession = Depends(get_session),
) -> list[cleanings]:
    # 아직 sqlmodel의 async session은 type hint와 관련해서 제대로 지원하지 않습니다.
    # 제대로 작성된게 맞는지 확인해보고 싶다면,
    # session.sync_session에서 type hint 관련해서만 확인해보면 됩니다.
    #
    # sync_session = session.sync_session
    # table = sync_session.exec(select(cleanings))
    # rows = table.all()
    table = await session.exec(select(cleanings))  # type: ignore
    rows = cast(list[cleanings], table.all())
    return rows


@router.post(
    "",
    response_model=cleaning_public,
    name="cleanings:create-cleaning",
    status_code=HTTP_201_CREATED,
)
async def create_new_cleaning(
    new_cleaning: cleaning_create = Body(..., embed=True),
    session: AsyncSession = Depends(get_session),
) -> cleanings:
    # data = cleanings.from_orm(new_cleaning) 으로 해도 가능
    # exclude_none=True, exclude_unset=True 옵션을 위해 parse_obj 사용
    # sqlmodel table=True 관련 validation 문제로 인해 validate사용
    data = cleanings.validate(
        new_cleaning.dict(
            exclude_none=True,
            exclude_unset=True,
        )
    )
    session.add(data)
    await session.flush()
    await session.commit()
    await session.refresh(data)

    return data


@router.get(
    "/{id}", response_model=cleaning_public, name="cleanings:get-cleaning-by-id"
)
async def get_cleaning_by_id(
    id: int = Path(..., ge=1),
    session: AsyncSession = Depends(get_session),
) -> cleanings:
    if (cleaning := await session.get(cleanings, id)) is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="No cleaning found with that id."
        )
    return cleaning


@router.patch(
    "/{id}",
    response_model=cleaning_public,
    name="cleanings:update-cleaning-by-id-as-patch",
)
async def update_cleaning_by_id_as_patch(
    id: int = Path(..., ge=1),
    update_cleaning: cleaning_update = Body(..., embed=True),
    session: AsyncSession = Depends(get_session),
) -> cleanings:
    if (cleaning := await session.get(cleanings, id)) is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="No cleaning found with that id."
        )

    # validate 관련 문제 해결 전까지는 이렇게..
    update_dict = update_cleaning.dict(exclude_unset=True)
    try:
        cleanings.validate(cleaning.dict() | update_dict)
    except ValidationError as exc:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail=orjson.loads(exc.json())
        )

    for attr, value in update_dict.items():
        setattr(cleaning, attr, value)

    session.add(cleaning.update())
    await session.flush()
    await session.commit()
    await session.refresh(cleaning)

    return cleaning


@router.delete("/{id}", response_model=int, name="cleanings:delete-cleaning-by-id")
async def delete_cleaning_by_id(
    id: int = Path(..., ge=1, title="The ID of the cleaning to delete."),
    session: AsyncSession = Depends(get_session),
) -> int:
    if (cleaning := await session.get(cleanings, id)) is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="No cleaning found with that id."
        )

    await session.delete(cleaning)
    await session.flush()
    await session.commit()

    return id


@router.put(
    "/{id}",
    response_model=cleaning_public,
    name="cleanings:update-cleaning-by-id-as-put",
)
async def update_cleaning_by_id_as_put(
    id: int = Path(..., ge=1),
    update_cleaning: cleaning_update = Body(..., embed=True),
    session: AsyncSession = Depends(get_session),
) -> cleanings:
    if (cleaning := await session.get(cleanings, id)) is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail="No cleaning found with that id."
        )

    try:
        new_cleaning = cleanings.validate(update_cleaning.dict(exclude_unset=True))
    except ValidationError as exc:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail=orjson.loads(exc.json())
        )

    for attr, value in new_cleaning.dict(exclude={"id"}).items():
        setattr(cleaning, attr, value)

    session.add(cleaning.update())
    await session.flush()
    await session.commit()
    await session.refresh(cleaning)

    return cleaning
