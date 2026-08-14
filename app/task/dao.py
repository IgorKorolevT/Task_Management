from sqlalchemy.ext.asyncio import AsyncSession
from app.common.dao import BaseDAO
from sqlalchemy import func, select
from app.task.models import Task, TaskStatus
from datetime import datetime, timezone

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

    @classmethod
    async def get_overdue(
            cls,
            session: AsyncSession,
    ) -> list[Task]:
        now = datetime.now(timezone.utc)

        query = (
            select(cls.model)
            .where(
                cls.model.deadline < now,
                cls.model.status.notin_(
                    (
                        TaskStatus.DONE,
                        TaskStatus.CANCELLED,
                    )
                ),
            )
            .order_by(
                cls.model.deadline.asc()
            )
        )

        result = await session.execute(query)

        return list(result.scalars().all())

    @classmethod
    async def get_statistics(
            cls,
            session: AsyncSession,
    ) -> dict:
        now = datetime.now(timezone.utc)

        # -------------------------
        # TOTAL
        # -------------------------

        total_result = await session.execute(
            select(func.count(cls.model.id))
        )

        total = total_result.scalar_one()

        # -------------------------
        # BY STATUS
        # -------------------------

        status_result = await session.execute(
            select(
                cls.model.status,
                func.count(cls.model.id),
            )
            .group_by(cls.model.status)
        )

        by_status = {
            status: count
            for status, count in status_result.all()
        }

        # -------------------------
        # BY PRIORITY
        # -------------------------

        priority_result = await session.execute(
            select(
                cls.model.priority,
                func.count(cls.model.id),
            )
            .group_by(cls.model.priority)
        )

        by_priority = {
            priority: count
            for priority, count in priority_result.all()
        }

        # -------------------------
        # OVERDUE
        # -------------------------

        overdue_result = await session.execute(
            select(func.count(cls.model.id))
            .where(
                cls.model.deadline < now,
                cls.model.status.notin_(
                    (
                        TaskStatus.DONE,
                        TaskStatus.CANCELLED,
                    )
                ),
            )
        )

        overdue = overdue_result.scalar_one()

        # -------------------------
        # ACTIVE
        # -------------------------

        active_result = await session.execute(
            select(func.count(cls.model.id))
            .where(
                cls.model.status.in_(
                    (
                        TaskStatus.BACKLOG,
                        TaskStatus.IN_PROGRESS,
                        TaskStatus.REVIEW,
                    )
                )
            )
        )

        active = active_result.scalar_one()

        return {
            "total": total,
            "by_status": by_status,
            "by_priority": by_priority,
            "overdue": overdue,
            "active": active,
        }