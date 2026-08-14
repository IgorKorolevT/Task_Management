from sqlalchemy.ext.asyncio import AsyncSession
from app.common.dao import BaseDAO
from sqlalchemy import func, select
from app.task.models import Task, TaskStatus


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

    @classmethod
    async def count_active_by_assignee(
            cls,
            session: AsyncSession,
            assignee_id: int,
    ) -> int:
        result = await session.execute(
            select(func.count(cls.model.id))
            .where(
                cls.model.assignee_id == assignee_id,
                cls.model.status.in_(
                    (
                        TaskStatus.BACKLOG,
                        TaskStatus.IN_PROGRESS,
                        TaskStatus.REVIEW,
                    )
                ),
            )
        )

        return result.scalar_one()
