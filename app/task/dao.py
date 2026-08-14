from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.dao import BaseDAO
from app.common.ensure_time import ensure_utc, now_utc
from app.task.models import (
    Task,
    TaskPriority,
    TaskStatus,
)
from app.task.schemas import (
    SortOrder,
    TaskFilter,
    TaskSortField,
)


class TaskDAO(BaseDAO[Task]):
    model = Task

    @classmethod
    async def get_by_id(
        cls,
        session: AsyncSession,
        object_id: int,
    ) -> Task | None:
        result = await session.execute(
            select(cls.model).where(
                cls.model.id == object_id
            )
        )

        return result.scalar_one_or_none()

    @classmethod
    async def count_active_by_assignee(
        cls,
        session: AsyncSession,
        assignee_id: int,
    ) -> int:
        result = await session.execute(
            select(func.count(cls.model.id)).where(
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
    async def get_filtered(
        cls,
        session: AsyncSession,
        filters: TaskFilter,
    ) -> tuple[list[Task], int]:
        query = select(cls.model)

        # -------------------------------------------------
        # Search
        # -------------------------------------------------

        if filters.search:
            search = f"%{filters.search}%"

            query = query.where(
                or_(
                    cls.model.title.ilike(search),
                    cls.model.description.ilike(search),
                )
            )

        # -------------------------------------------------
        # Filters
        # -------------------------------------------------

        if filters.status is not None:
            query = query.where(
                cls.model.status == filters.status
            )

        if filters.priority is not None:
            query = query.where(
                cls.model.priority == filters.priority
            )

        if filters.assignee_id is not None:
            query = query.where(
                cls.model.assignee_id == filters.assignee_id
            )

        if filters.deadline_from is not None:
            query = query.where(
                cls.model.deadline
                >= ensure_utc(filters.deadline_from)
            )

        if filters.deadline_to is not None:
            query = query.where(
                cls.model.deadline
                <= ensure_utc(filters.deadline_to)
            )

        # -------------------------------------------------
        # Total
        # -------------------------------------------------

        count_query = select(
            func.count()
        ).select_from(
            query.subquery()
        )

        count_result = await session.execute(
            count_query
        )

        total = count_result.scalar_one()

        # -------------------------------------------------
        # Priority order
        # High -> Medium -> Low
        # -------------------------------------------------

        priority_order = case(
            (cls.model.priority == TaskPriority.HIGH, 1),
            (cls.model.priority == TaskPriority.MEDIUM, 2),
            (cls.model.priority == TaskPriority.LOW, 3),
            else_=99,
        )

        # -------------------------------------------------
        # Sorting
        # -------------------------------------------------

        if filters.sort_by == TaskSortField.DEFAULT:
            query = query.order_by(
                priority_order.asc(),
                cls.model.deadline.asc(),
            )

        elif filters.sort_by == TaskSortField.CREATED_AT:
            if filters.sort_order == SortOrder.DESC:
                query = query.order_by(
                    cls.model.created_at.desc()
                )
            else:
                query = query.order_by(
                    cls.model.created_at.asc()
                )

        elif filters.sort_by == TaskSortField.DEADLINE:
            if filters.sort_order == SortOrder.DESC:
                query = query.order_by(
                    cls.model.deadline.desc()
                )
            else:
                query = query.order_by(
                    cls.model.deadline.asc()
                )

        elif filters.sort_by == TaskSortField.PRIORITY:
            if filters.sort_order == SortOrder.DESC:
                query = query.order_by(
                    priority_order.desc()
                )
            else:
                query = query.order_by(
                    priority_order.asc()
                )

        # -------------------------------------------------
        # Pagination
        # -------------------------------------------------

        offset = (
            (filters.page - 1)
            * filters.page_size
        )

        query = query.offset(offset).limit(
            filters.page_size
        )

        result = await session.execute(query)

        tasks = list(result.scalars().all())

        return tasks, total

    @classmethod
    async def get_overdue(
        cls,
        session: AsyncSession,
    ) -> list[Task]:
        query = (
            select(cls.model)
            .where(
                cls.model.deadline < now_utc(),
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
        now = now_utc()

        # -------------------------------------------------
        # Total
        # -------------------------------------------------

        total_result = await session.execute(
            select(func.count(cls.model.id))
        )

        total = total_result.scalar_one()

        # -------------------------------------------------
        # By status
        # -------------------------------------------------

        status_result = await session.execute(
            select(
                cls.model.status,
                func.count(cls.model.id),
            ).group_by(
                cls.model.status
            )
        )

        by_status = {
            task_status: count
            for task_status, count
            in status_result.all()
        }

        # -------------------------------------------------
        # By priority
        # -------------------------------------------------

        priority_result = await session.execute(
            select(
                cls.model.priority,
                func.count(cls.model.id),
            ).group_by(
                cls.model.priority
            )
        )

        by_priority = {
            priority: count
            for priority, count
            in priority_result.all()
        }

        # -------------------------------------------------
        # Overdue
        # -------------------------------------------------

        overdue_result = await session.execute(
            select(func.count(cls.model.id)).where(
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

        # -------------------------------------------------
        # Active
        # -------------------------------------------------

        active_result = await session.execute(
            select(func.count(cls.model.id)).where(
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