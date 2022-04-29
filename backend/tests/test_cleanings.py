import pytest
from app.models.cleaning import cleaning_create, cleanings
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

# decorate all tests with @pytest.mark.asyncio
pytestmark = pytest.mark.asyncio


@pytest.fixture
def new_cleaning():
    return cleaning_create.parse_obj(
        dict(
            name="test cleaning",
            description="test description",
            price=0.00,
            cleaning_type="spot_clean",
        )
    )


class TestCleaningsRoutes:
    async def test_routes_exist(self, app: FastAPI, client: AsyncClient) -> None:
        res = await client.post(app.url_path_for("cleanings:create-cleaning"), json={})
        assert res.status_code != HTTP_404_NOT_FOUND

    async def test_invalid_input_raises_error(
        self, app: FastAPI, client: AsyncClient
    ) -> None:
        res = await client.post(app.url_path_for("cleanings:create-cleaning"), json={})
        assert res.status_code == HTTP_422_UNPROCESSABLE_ENTITY


class TestCreateCleaning:
    async def test_valid_input_creates_cleaning(
        self, app: FastAPI, client: AsyncClient, new_cleaning: cleaning_create
    ) -> None:
        res = await client.post(
            app.url_path_for("cleanings:create-cleaning"),
            json={"new_cleaning": new_cleaning.dict()},
        )
        assert res.status_code == HTTP_201_CREATED

        created_cleaning = cleaning_create(**res.json())
        assert created_cleaning == new_cleaning

    @pytest.mark.parametrize(
        "invalid_payload, status_code",
        (
            (None, 422),
            ({}, 422),
            ({"name": "test_name"}, 422),
            ({"price": 10.00}, 422),
            ({"name": "test_name", "description": "test"}, 422),
        ),
    )
    async def test_invalid_input_raises_error(
        self, app: FastAPI, client: AsyncClient, invalid_payload: dict, status_code: int
    ) -> None:
        res = await client.post(
            app.url_path_for("cleanings:create-cleaning"),
            json={"new_cleaning": invalid_payload},
        )
        assert res.status_code == status_code


@pytest.fixture
async def test_cleaning(engine: AsyncEngine) -> cleanings:
    new_cleaning_create = cleaning_create.parse_obj(
        dict(
            name="fake cleaning name",
            description="fake cleaning description",
            price=9.99,
            cleaning_type="spot_clean",
        )
    )
    new_cleaning = cleanings.from_orm(new_cleaning_create)
    async with AsyncSession(engine, autocommit=False) as session:
        session.add(new_cleaning)
        await session.commit()
        await session.refresh(new_cleaning)

    return new_cleaning


class TestGetCleaning:
    async def test_get_cleaning_by_id(
        self, app: FastAPI, client: AsyncClient, test_cleaning: cleanings
    ) -> None:
        print(test_cleaning)
        res = await client.get(
            app.url_path_for("cleanings:get-cleaning-by-id", id=str(test_cleaning.id))
        )
        assert res.status_code == HTTP_200_OK
        cleaning = cleanings.parse_obj(res.json())
        assert cleaning == test_cleaning

    @pytest.mark.parametrize(
        "id, status_code",
        (
            (500, 404),
            (-1, 422),
            (None, 422),
        ),
    )
    async def test_wrong_id_returns_error(
        self, app: FastAPI, client: AsyncClient, id: int, status_code: int
    ) -> None:
        res = await client.get(
            app.url_path_for("cleanings:get-cleaning-by-id", id=str(id))
        )
        assert res.status_code == status_code
