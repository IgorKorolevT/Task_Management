from datetime import datetime, timezone
from math import ceil

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.ensure_time import ensure_utc, now_utc
from app.task.dao import TaskDAO
from app.task.models import (
    Task,
    TaskPriority,
    TaskStatus,
)
from app.task.schemas import (
    TaskCreate,
    TaskFilter,
    TaskListResponse,
    TaskStatisticsResponse,
    TaskStatusUpdate,
    TaskUpdate,
)
from app.user.dao import UserDAO


class TaskService:

    @staticmethod
    async def create(
        session: AsyncSession,
        data: TaskCreate,
        author_id: int,
    ) -> Task:

        deadline = ensure_utc(data.deadline)

        if deadline <= now_utc():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Deadline must be in the future",
            )

        if data.assignee_id is not None:
            assignee = await UserDAO.get_by_id(
                session,
                data.assignee_id,
            )

            if not assignee or not assignee.is_active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Assignee not found or inactive",
                )

            active_tasks = (
                await TaskDAO.count_active_by_assignee(
                    session,
                    data.assignee_id,
                )
            )

            if active_tasks >= 10:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "User cannot have more than "
                        "10 active tasks"
                    ),
                )

        task = await TaskDAO.create(
            session,
            title=data.title,
            description=data.description,
            priority=data.priority,
            assignee_id=data.assignee_id,
            author_id=author_id,
            deadline=deadline,
        )

        await session.commit()
        await session.refresh(task)

        return task

    @staticmethod
    async def get_by_id(
        session: AsyncSession,
        task_id: int,
    ) -> Task:
        task = await TaskDAO.get_by_id(
            session,
            task_id,
        )

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        return task

    @staticmethod
    async def update(
        session: AsyncSession,
        task_id: int,
        data: TaskUpdate,
    ) -> Task:

        task = await TaskService.get_by_id(
            session,
            task_id,
        )

        if task.status in (
            TaskStatus.DONE,
            TaskStatus.CANCELLED,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Task cannot be edited "
                    "in its current status"
                ),
            )

        update_data = data.model_dump(
            exclude_unset=True,
        )

        if "deadline" in update_data:
            deadline = ensure_utc(
                update_data["deadline"]
            )

            if deadline <= now_utc():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Deadline must be in the future",
                )

            update_data["deadline"] = deadline

        if "assignee_id" in update_data:

            if task.status in (
                TaskStatus.REVIEW,
                TaskStatus.DONE,
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Assignee cannot be changed "
                        "in Review or Done status"
                    ),
                )

            assignee_id = update_data["assignee_id"]

            if assignee_id is not None:
                assignee = await UserDAO.get_by_id(
                    session,
                    assignee_id,
                )

                if not assignee or not assignee.is_active:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Assignee not found or inactive",
                    )

                active_tasks = (
                    await TaskDAO.count_active_by_assignee(
                        session,
                        assignee_id,
                    )
                )

                if (
                    active_tasks >= 10
                    and assignee_id != task.assignee_id
                ):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=(
                            "User cannot have more than "
                            "10 active tasks"
                        ),
                    )

        task = await TaskDAO.update(
            session,
            task,
            **update_data,
        )

        await session.commit()
        await session.refresh(task)

        return task

    @staticmethod
    async def delete(
        session: AsyncSession,
        task_id: int,
    ) -> None:

        task = await TaskService.get_by_id(
            session,
            task_id,
        )

        if task.status in (
            TaskStatus.IN_PROGRESS,
            TaskStatus.REVIEW,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Task cannot be deleted "
                    "in its current status"
                ),
            )

        await TaskDAO.delete(
            session,
            task,
        )

        await session.commit()

    @staticmethod
    async def change_status(
        session: AsyncSession,
        task_id: int,
        data: TaskStatusUpdate,
    ) -> Task:

        task = await TaskService.get_by_id(
            session,
            task_id,
        )

        allowed_transitions = {
            TaskStatus.BACKLOG: {
                TaskStatus.IN_PROGRESS,
                TaskStatus.CANCELLED,
            },
            TaskStatus.IN_PROGRESS: {
                TaskStatus.REVIEW,
                TaskStatus.CANCELLED,
            },
            TaskStatus.REVIEW: {
                TaskStatus.DONE,
                TaskStatus.CANCELLED,
            },
            TaskStatus.DONE: set(),
            TaskStatus.CANCELLED: set(),
        }

        new_status = data.status

        if new_status not in allowed_transitions[
            task.status
        ]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Cannot change status from "
                    f"{task.status.value} to "
                    f"{new_status.value}"
                ),
            )

        if new_status == TaskStatus.DONE:

            if task.assignee_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Task must have an assignee "
                        "before completion"
                    ),
                )

            if ensure_utc(task.deadline) <= now_utc():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "Cannot complete task "
                        "after deadline"
                    ),
                )

        task = await TaskDAO.update(
            session,
            task,
            status=new_status,
        )

        await session.commit()
        await session.refresh(task)

        return task

    @staticmethod
    async def get_filtered(
        session: AsyncSession,
        filters: TaskFilter,
    ) -> TaskListResponse:

        tasks, total = await TaskDAO.get_filtered(
            session,
            filters,
        )

        pages = (
            ceil(total / filters.page_size)
            if total
            else 0
        )

        return TaskListResponse(
            items=tasks,
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            pages=pages,
        )

    @staticmethod
    async def get_overdue(
        session: AsyncSession,
    ) -> list[Task]:

        return await TaskDAO.get_overdue(
            session
        )

    @staticmethod
    async def get_statistics(
        session: AsyncSession,
    ) -> TaskStatisticsResponse:

        statistics = await TaskDAO.get_statistics(
            session
        )

        by_status = {
            task_status: statistics["by_status"].get(
                task_status,
                0,
            )
            for task_status in TaskStatus
        }

        by_priority = {
            priority: statistics["by_priority"].get(
                priority,
                0,
            )
            for priority in TaskPriority
        }

        return TaskStatisticsResponse(
            total=statistics["total"],
            by_status=by_status,
            by_priority=by_priority,
            overdue=statistics["overdue"],
            active=statistics["active"],
        )
