from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.user.auth import hash_password, verify_password
from app.user.dao import UserDAO
from app.user.models import User
from app.user.schemas import UserCreate, UserUpdate


class UserService:

    @staticmethod
    async def register(
        db: AsyncSession,
        user_data: UserCreate,
    ) -> User:
        existing_user = await UserDAO.get_by_username(
            db,
            user_data.username,
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )

        existing_email = await UserDAO.get_by_email(
            db,
            user_data.email,
        )

        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        user = await UserDAO.create(
            db,
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hash_password(
                user_data.password
            ),
        )

        await db.commit()

        return user

    @staticmethod
    async def authenticate(
        db: AsyncSession,
        username: str,
        password: str,
    ) -> User | None:
        user = await UserDAO.get_by_username_or_email(
            db,
            username,
        )

        if not user:
            return None

        if not user.is_active:
            return None

        if not verify_password(
            password,
            user.hashed_password,
        ):
            return None

        return user

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        user_id: int,
    ) -> User:
        user = await UserDAO.get_active_by_id(
            db,
            user_id,
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return user

    @staticmethod
    async def update(
        db: AsyncSession,
        user: User,
        user_data: UserUpdate,
    ) -> User:
        update_data = user_data.model_dump(
            exclude_unset=True,
        )

        if not update_data:
            return user

        if "username" in update_data:
            existing_user = await UserDAO.get_by_username(
                db,
                update_data["username"],
            )

            if (
                existing_user
                and existing_user.id != user.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already registered",
                )

        if "email" in update_data:
            existing_email = await UserDAO.get_by_email(
                db,
                update_data["email"],
            )

            if (
                existing_email
                and existing_email.id != user.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered",
                )

        if "password" in update_data:
            password = update_data.pop("password")

            update_data["hashed_password"] = (
                hash_password(password)
            )

        user = await UserDAO.update(
            db,
            user,
            **update_data,
        )

        await db.commit()

        return user

    @staticmethod
    async def delete(
        db: AsyncSession,
        user: User,
    ) -> None:
        user.is_active = False

        await db.commit()