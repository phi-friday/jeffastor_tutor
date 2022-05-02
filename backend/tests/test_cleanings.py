from contextlib import suppress
from decimal import Decimal, InvalidOperation

import orjson
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
            json={"new_cleaning": orjson.loads(new_cleaning.json())},
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
    new_cleaning = cleanings.validate(new_cleaning_create)
    async with AsyncSession(engine, autocommit=False) as session:
        session.add(new_cleaning)
        await session.commit()
        await session.refresh(new_cleaning)

    return new_cleaning


class TestGetCleaning:
    async def test_get_cleaning_by_id(
        self, app: FastAPI, client: AsyncClient, test_cleaning: cleanings
    ) -> None:
        res = await client.get(
            app.url_path_for("cleanings:get-cleaning-by-id", id=str(test_cleaning.id))
        )
        assert res.status_code == HTTP_200_OK
        cleaning = cleanings.validate(res.json())
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

    async def test_get_all_cleanings_returns_valid_response(
        self, app: FastAPI, client: AsyncClient, test_cleaning: cleanings
    ) -> None:
        res = await client.get(app.url_path_for("cleanings:get-all-cleanings"))
        assert res.status_code == HTTP_200_OK
        assert isinstance((json := res.json()), list)
        assert len(json) > 0
        all_cleanings = [cleanings.validate(l) for l in json]
        assert test_cleaning in all_cleanings


class TestPatchCleaning:
    @pytest.mark.parametrize(
        "attrs_to_change, values",
        (
            (["name"], ["new fake cleaning name"]),
            (["description"], ["new fake cleaning description"]),
            (["price"], [3.14]),
            (["cleaning_type"], ["full_clean"]),
            (
                ["name", "description"],
                [
                    "extra new fake cleaning name",
                    "extra new fake cleaning description",
                ],
            ),
            (["price", "cleaning_type"], [42.00, "dust_up"]),
        ),
    )
    async def test_update_cleaning_with_valid_input(
        self,
        app: FastAPI,
        client: AsyncClient,
        test_cleaning: cleanings,
        attrs_to_change: list[str],
        values: list[str | int | float],
    ) -> None:
        update_cleaning = {"update_cleaning": dict(zip(attrs_to_change, values))}

        res = await client.patch(
            app.url_path_for(
                "cleanings:update-cleaning-by-id-as-patch",
                id=str(test_cleaning.id),
            ),
            json=update_cleaning,
        )
        assert res.status_code == HTTP_200_OK
        updated_cleaning = cleanings.validate(res.json())
        assert (
            updated_cleaning.id == test_cleaning.id
        )  # make sure it's the same cleaning
        # make sure that any attribute we updated has changed to the correct value
        for attr, value in zip(attrs_to_change, values):
            attr_to_change = getattr(updated_cleaning, attr)
            assert attr_to_change != getattr(test_cleaning, attr)
            if attr == "price":
                with suppress(InvalidOperation, ValueError):
                    value = Decimal(f"{float(value):.2f}")
            assert attr_to_change == value
        # make sure that no other attributes' values have changed
        for attr, value in updated_cleaning.dict().items():
            if attr not in attrs_to_change:
                assert getattr(test_cleaning, attr) == value

    @pytest.mark.parametrize(
        "id, payload, status_code",
        (
            (-1, {"name": "test"}, 422),
            (0, {"name": "test2"}, 422),
            (500, {"name": "test3"}, 404),
            (1, None, 422),
            (1, {"cleaning_type": "invalid cleaning type"}, 422),
            (1, {"cleaning_type": None}, 422),
        ),
    )
    async def test_update_cleaning_with_invalid_input_throws_error(
        self,
        app: FastAPI,
        client: AsyncClient,
        id: int,
        payload: dict,
        status_code: int,
    ) -> None:
        update_cleaning = {"update_cleaning": payload}
        res = await client.patch(
            app.url_path_for("cleanings:update-cleaning-by-id-as-patch", id=str(id)),
            json=update_cleaning,
        )
        assert res.status_code == status_code


class TestDeleteCleaning:
    async def test_can_delete_cleaning_successfully(
        self,
        app: FastAPI,
        client: AsyncClient,
        test_cleaning: cleanings,
    ) -> None:
        # delete the cleaning
        res = await client.delete(
            app.url_path_for(
                "cleanings:delete-cleaning-by-id", id=str(test_cleaning.id)
            ),
        )
        assert res.status_code == HTTP_200_OK
        # ensure that the cleaning no longer exists
        res = await client.get(
            app.url_path_for("cleanings:get-cleaning-by-id", id=str(test_cleaning.id)),
        )
        assert res.status_code == HTTP_404_NOT_FOUND

    @pytest.mark.parametrize(
        "id, status_code",
        (
            (500, 404),
            (0, 422),
            (-1, 422),
            (None, 422),
        ),
    )
    async def test_delete_cleaning_with_invalid_input_throws_error(
        self,
        app: FastAPI,
        client: AsyncClient,
        test_cleaning: cleanings,
        id: int,
        status_code: int,
    ) -> None:
        res = await client.delete(
            app.url_path_for("cleanings:delete-cleaning-by-id", id=str(id)),
        )
        assert res.status_code == status_code


class TestPutCleaning:
    @pytest.mark.parametrize(
        "attrs_to_change, values",
        (
            (
                ["name", "description", "price"],
                [
                    "new fake cleaning name",
                    "new fake cleaning description",
                    "123.1",
                ],
            ),
            (
                ["name", "price", "cleaning_type"],
                ["extra new fake cleaning name", 15555.51, "dust_up"],
            ),
            (
                ["name", "price"],
                ["extra new fake cleaning name", Decimal("2.12")],
            ),
        ),
    )
    async def test_update_cleaning_with_valid_input(
        self,
        app: FastAPI,
        client: AsyncClient,
        test_cleaning: cleanings,
        attrs_to_change: list[str],
        values: list[str | int | float],
    ) -> None:
        update_cleaning = {"update_cleaning": dict(zip(attrs_to_change, values))}

        print(orjson.loads(orjson.dumps(update_cleaning, default=str)))
        res = await client.put(
            app.url_path_for(
                "cleanings:update-cleaning-by-id-as-put",
                id=str(test_cleaning.id),
            ),
            json=orjson.loads(orjson.dumps(update_cleaning, default=str)),
        )
        assert res.status_code == HTTP_200_OK
        updated_cleaning = cleanings.validate(res.json())
        assert updated_cleaning.id == test_cleaning.id

        for attr, value in update_cleaning["update_cleaning"].items():
            if attr == "price":
                with suppress(InvalidOperation, ValueError):
                    value = Decimal(f"{float(value):.2f}")
            assert value == getattr(updated_cleaning, attr)

        for attr, value in updated_cleaning.dict(exclude={"id"}).items():
            if attr not in attrs_to_change:
                assert value == cleanings.__fields__[attr].default

    @pytest.mark.parametrize(
        "id, payload, status_code",
        (
            (-1, {"name": "test"}, 422),
            (0, {"name": "test2", "price": 123}, 422),
            (500, {"name": "test3", "price": 33.3}, 404),
            (1, None, 422),
            (
                1,
                {
                    "name": "test5",
                    "price": "123.3",
                    "cleaning_type": "invalid cleaning type",
                },
                422,
            ),
            (1, {"name": "test6", "price": 123.3, "cleaning_type": None}, 422),
        ),
    )
    async def test_update_cleaning_with_invalid_input_throws_error(
        self,
        app: FastAPI,
        client: AsyncClient,
        id: int,
        payload: dict,
        status_code: int,
    ) -> None:
        update_cleaning = {"update_cleaning": payload}
        res = await client.patch(
            app.url_path_for("cleanings:update-cleaning-by-id-as-put", id=str(id)),
            json=update_cleaning,
        )
        assert res.status_code == status_code
