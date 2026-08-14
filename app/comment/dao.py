from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.comment.models import Comment
from app.common.dao import BaseDAO


class CommentDAO(BaseDAO[Comment]):
    model = Comment

    @classmethod
    async def get_by_task_id(
        cls,
        session: AsyncSession,
        task_id: int,
    ) -> list[Comment]:
        result = await session.execute(
            select(cls.model)
            .where(cls.model.task_id == task_id)
            .order_by(cls.model.created_at.asc())
        )

        return list(result.scalars().all())