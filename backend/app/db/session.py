from typing import (
    Any,
    AsyncIterator,
    Literal,
    Mapping,
    Optional,
    Sequence,
    Type,
    TypeVar,
    Union,
    overload,
)

from fastapi import Depends, Request
from sqlalchemy import util
from sqlalchemy.ext.asyncio.engine import AsyncEngine
from sqlalchemy.sql.base import Executable as _Executable
from sqlmodel.engine.result import Result, ScalarResult
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.base import Executable
from sqlmodel.sql.expression import Select, SelectOfScalar

_TSelectParam = TypeVar("_TSelectParam")


class async_session(AsyncSession):
    # sqlmodel.orm.session.Session
    @overload
    async def exec(
        self,
        statement: Select[_TSelectParam],
        *,
        params: Optional[Union[Mapping[str, Any], Sequence[Mapping[str, Any]]]] = None,
        execution_options: Mapping[str, Any] = util.EMPTY_DICT,
        bind_arguments: Optional[Mapping[str, Any]] = None,
        _parent_execute_state: Optional[Any] = None,
        _add_event: Optional[Any] = None,
        **kw: Any,
    ) -> Result[_TSelectParam]:
        ...

    @overload
    async def exec(
        self,
        statement: SelectOfScalar[_TSelectParam],
        *,
        params: Optional[Union[Mapping[str, Any], Sequence[Mapping[str, Any]]]] = None,
        execution_options: Mapping[str, Any] = util.EMPTY_DICT,
        bind_arguments: Optional[Mapping[str, Any]] = None,
        _parent_execute_state: Optional[Any] = None,
        _add_event: Optional[Any] = None,
        **kw: Any,
    ) -> ScalarResult[_TSelectParam]:
        ...

    async def exec(
        self,
        statement: Union[
            Select[_TSelectParam],
            SelectOfScalar[_TSelectParam],
            Executable[_TSelectParam],
        ],
        *,
        params: Optional[Union[Mapping[str, Any], Sequence[Mapping[str, Any]]]] = None,
        execution_options: Mapping[str, Any] = util.EMPTY_DICT,
        bind_arguments: Optional[Mapping[str, Any]] = None,
        _parent_execute_state: Optional[Any] = None,
        _add_event: Optional[Any] = None,
        **kw: Any,
    ) -> Union[Result[_TSelectParam], ScalarResult[_TSelectParam]]:
        """
        sqlmodel.orm.session.Session
        """
        return await super().exec(
            statement,  # type: ignore
            params=params,
            execution_options=execution_options,
            bind_arguments=bind_arguments,
            _parent_execute_state=_parent_execute_state,
            _add_event=_add_event,
            **kw,
        )

    async def execute(
        self,
        statement: _Executable,
        params: Optional[Union[Mapping[str, Any], Sequence[Mapping[str, Any]]]] = None,
        execution_options: Optional[Mapping[str, Any]] = util.EMPTY_DICT,
        bind_arguments: Optional[Mapping[str, Any]] = None,
        _parent_execute_state: Optional[Any] = None,
        _add_event: Optional[Any] = None,
        **kw: Any,
    ) -> Result[Any]:
        """
        sqlmodel.orm.session.Session
        ***

        🚨 You probably want to use `session.exec()` instead of `session.execute()`.

        This is the original SQLAlchemy `session.execute()` method that returns objects
        of type `Row`, and that you have to call `scalars()` to get the model objects.

        For example:

        ```Python
        heroes = session.execute(select(Hero)).scalars().all()
        ```

        instead you could use `exec()`:

        ```Python
        heroes = session.exec(select(Hero)).all()
        ```
        """
        return await super().execute(  # type: ignore
            statement,
            params=params,
            execution_options=execution_options,
            bind_arguments=bind_arguments,
            _parent_execute_state=_parent_execute_state,
            _add_event=_add_event,
            **kw,
        )

    async def get(
        self,
        entity: Type[_TSelectParam],
        ident: Any,
        options: Optional[Sequence[Any]] = None,
        populate_existing: bool = False,
        with_for_update: Optional[Union[Literal[True], Mapping[str, Any]]] = None,
        identity_token: Optional[Any] = None,
    ) -> Optional[_TSelectParam]:
        """
        sqlmodel.orm.session.Session
        """
        return await super().get(
            entity,
            ident,
            options=options,
            populate_existing=populate_existing,
            with_for_update=with_for_update,
            identity_token=identity_token,
        )


async def get_database(request: Request) -> AsyncEngine:
    if (engine := getattr(request.app.state, "_db", None)) is None:
        raise AttributeError("there is no database engine in request as state")
    return engine


async def get_session(
    engine: AsyncEngine = Depends(get_database),
) -> AsyncIterator[async_session]:
    async with async_session(engine, autoflush=False, autocommit=False) as session:
        yield session
