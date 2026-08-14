from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.task.dao import TaskDAO
from app.task.models import Task
from app.task.schemas import TaskCreate, TaskUpdate
from app.user.dao import UserDAO


class TaskService:

    @staticmethod
    async def create(
        session: AsyncSession,
        data: TaskCreate,
        author_id: int,
    ) -> Task:
        now = datetime.now(timezone.utc)

        if data.deadline <= now:
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

        task = await TaskDAO.create(
            session,
            title=data.title,
            description=data.description,
            priority=data.priority,
            assignee_id=data.assignee_id,
            author_id=author_id,
            deadline=data.deadline,
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
    async def get_all(
        session: AsyncSession,
    ) -> list[Task]:
        return await TaskDAO.get_all(session)

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

        update_data = data.model_dump(
            exclude_unset=True,
        )

        if "deadline" in update_data:
            deadline = update_data["deadline"]

            if deadline <= datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Deadline must be in the future",
                )

        if "assignee_id" in update_data:
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

        await TaskDAO.delete(
            session,
            task,
        )

        await session.commit()