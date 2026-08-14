from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.dao import BaseDAO
from app.user.models import User


class UserDAO(BaseDAO[User]):
    model = User

    @classmethod
    async def get_by_username(
        cls,
        session: AsyncSession,
        username: str,
    ) -> User | None:
        result = await session.execute(
            select(cls.model).where(
                cls.model.username == username
            )
        )

        return result.scalar_one_or_none()

    @classmethod
    async def get_by_email(
        cls,
        session: AsyncSession,
        email: str,
    ) -> User | None:
        result = await session.execute(
            select(cls.model).where(
                cls.model.email == email
            )
        )

        return result.scalar_one_or_none()

    @classmethod
    async def get_by_username_or_email(
        cls,
        session: AsyncSession,
        value: str,
    ) -> User | None:
        result = await session.execute(
            select(cls.model).where(
                (cls.model.username == value)
                | (cls.model.email == value)
            )
        )

        return result.scalar_one_or_none()

    @classmethod
    async def get_active_by_id(
        cls,
        session: AsyncSession,
        user_id: int,
    ) -> User | None:
        result = await session.execute(
            select(cls.model).where(
                cls.model.id == user_id,
                cls.model.is_active.is_(True),
            )
        )

        return result.scalar_one_or_none()