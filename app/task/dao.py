from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.dao import BaseDAO
from app.task.models import Task


class TaskDAO(BaseDAO[Task]):
    model = Task

    @classmethod
    async def get_by_id(
        cls,
        session: AsyncSession,
        object_id: int,
    ) -> Task | None:
        result = await session.execute(
            select(cls.model)
            .where(cls.model.id == object_id)
        )

        return result.scalar_one_or_none()