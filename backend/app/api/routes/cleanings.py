from fastapi import APIRouter, Body, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.status import HTTP_201_CREATED

from ...db.session import get_session
from ...models.cleaning import cleaning_create, cleaning_public, cleanings

router = APIRouter()


@router.get("/")
async def get_all_cleanings() -> list[dict]:
    cleanings = [
        {
            "id": 1,
            "name": "My house",
            "cleaning_type": "full_clean",
            "price_per_hour": 29.99,
        },
        {
            "id": 2,
            "name": "Someone else's house",
            "cleaning_type": "spot_clean",
            "price_per_hour": 19.99,
        },
    ]
    return cleanings


@router.post(
    "/",
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
    data = cleanings.parse_obj(
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
