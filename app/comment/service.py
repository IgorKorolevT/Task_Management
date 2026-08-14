from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from app.comment.dao import CommentDAO
from app.comment.models import Comment
from app.comment.schemas import CommentCreate
from app.task.dao import TaskDAO


class CommentService:

    @staticmethod
    async def create(
        session: AsyncSession,
        task_id: int,
        author_id: int,
        data: CommentCreate,
    ) -> Comment:
        task = await TaskDAO.get_by_id(
            session,
            task_id,
        )

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        comment = await CommentDAO.create(
            session,
            task_id=task_id,
            author_id=author_id,
            content=data.content,
        )

        await session.commit()
        await session.refresh(comment)

        return comment

    @staticmethod
    async def get_by_task(
        session: AsyncSession,
        task_id: int,
    ) -> list[Comment]:
        task = await TaskDAO.get_by_id(
            session,
            task_id,
        )

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        return await CommentDAO.get_by_task_id(
            session,
            task_id,
        )


