from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.ensure_time import ensure_utc
from app.common.dao import BaseDAO
from app.task.models import Task, TaskPriority, TaskStatus
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
    async def get_filtered(
            cls,
            session: AsyncSession,
            filters: TaskFilter,
    ) -> tuple[list[Task], int]:

        query = select(cls.model)

        # SEARCH

        if filters.search:
            search = f"%{filters.search}%"

            query = query.where(
                or_(
                    cls.model.title.ilike(search),
                    cls.model.description.ilike(search),
                )
            )

        # FILTERS

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
                cls.model.deadline >= ensure_utc(filters.deadline_from)
            )

        if filters.deadline_to is not None:
            query = query.where(
                cls.model.deadline <= ensure_utc(filters.deadline_to)
            )

        # TOTAL

        count_query = select(
            func.count()
        ).select_from(
            query.subquery()
        )

        count_result = await session.execute(count_query)
        total = count_result.scalar_one()

        # SORTING

        priority_order = case(
            (cls.model.priority == TaskPriority.HIGH, 1),
            (cls.model.priority == TaskPriority.MEDIUM, 2),
            (cls.model.priority == TaskPriority.LOW, 3),
            else_=99,
        )

        if filters.sort_by == TaskSortField.DEFAULT:
            query = query.order_by(
                priority_order.asc(),
                cls.model.deadline.asc(),
            )

        elif filters.sort_by == TaskSortField.CREATED_AT:
            order = (
                cls.model.created_at.desc()
                if filters.sort_order == SortOrder.DESC
                else cls.model.created_at.asc()
            )

            query = query.order_by(order)

        elif filters.sort_by == TaskSortField.DEADLINE:
            order = (
                cls.model.deadline.desc()
                if filters.sort_order == SortOrder.DESC
                else cls.model.deadline.asc()
            )

            query = query.order_by(order)

        elif filters.sort_by == TaskSortField.PRIORITY:
            order = (
                priority_order.desc()
                if filters.sort_order == SortOrder.DESC
                else priority_order.asc()
            )

            query = query.order_by(order)

        # PAGINATION

        offset = (filters.page - 1) * filters.page_size

        query = query.offset(offset).limit(filters.page_size)

        result = await session.execute(query)

        tasks = list(result.scalars().all())

        return tasks, total
