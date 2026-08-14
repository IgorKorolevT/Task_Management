from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker


ModelType = TypeVar("ModelType")


class BaseDAO(Generic[ModelType]):
    model: type[ModelType]

    @classmethod
    def get_async_session_context(cls):
        return async_session_maker()

    @classmethod
    async def get_by_id(
        cls,
        session: AsyncSession,
        object_id: int,
    ) -> ModelType | None:
        result = await session.execute(
            select(cls.model).where(
                cls.model.id == object_id
            )
        )

        return result.scalar_one_or_none()

    @classmethod
    async def get_all(
        cls,
        session: AsyncSession,
    ) -> list[ModelType]:
        result = await session.execute(
            select(cls.model)
        )

        return list(result.scalars().all())

    @classmethod
    async def create(
        cls,
        session: AsyncSession,
        **data: Any,
    ) -> ModelType:
        obj = cls.model(**data)

        session.add(obj)

        await session.flush()
        await session.refresh(obj)

        return obj

    @classmethod
    async def update(
        cls,
        session: AsyncSession,
        obj: ModelType,
        **data: Any,
    ) -> ModelType:
        for field, value in data.items():
            setattr(obj, field, value)

        await session.flush()
        await session.refresh(obj)

        return obj

    @classmethod
    async def delete(
        cls,
        session: AsyncSession,
        obj: ModelType,
    ) -> None:
        await session.delete(obj)
        await session.flush()