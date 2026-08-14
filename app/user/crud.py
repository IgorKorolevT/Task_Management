from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from app.user.models import User
from app.user.schemas import UserCreate, UserUpdate
from app.user.auth import hash_password, verify_password
from app.logger import logger


async def create_user(db: AsyncSession, user: UserCreate):
    """Create new user"""
    try:
        db_user = User(
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            hashed_password=hash_password(user.password),
            is_active=True
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        logger.info(f"User created: {user.username}")
        return db_user
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating user: {e}")
        raise


async def get_user_by_id(db: AsyncSession, user_id: int):
    """Get user by ID"""
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error getting user by id: {e}")
        raise


async def get_user_by_username(db: AsyncSession, username: str):
    """Get user by username"""
    try:
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error getting user by username: {e}")
        raise


async def get_user_by_email(db: AsyncSession, email: str):
    """Get user by email"""
    try:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    except Exception as e:
        logger.error(f"Error getting user by email: {e}")
        raise


async def authenticate_user(db: AsyncSession, username: str, password: str):
    """Authenticate user by username and password"""
    try:
        user = await get_user_by_username(db, username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    except Exception as e:
        logger.error(f"Error authenticating user: {e}")
        raise


async def update_user(db: AsyncSession, user_id: int, user_update: UserUpdate):
    """Update user"""
    try:
        db_user = await get_user_by_id(db, user_id)
        if not db_user:
            return None
        
        update_data = user_update.model_dump(exclude_unset=True)
        
        if "password" in update_data and update_data["password"]:
            update_data["hashed_password"] = hash_password(update_data.pop("password"))
        else:
            update_data.pop("password", None)
        
        for key, value in update_data.items():
            setattr(db_user, key, value)
        
        await db.commit()
        await db.refresh(db_user)
        logger.info(f"User updated: {user_id}")
        return db_user
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating user: {e}")
        raise


async def delete_user(db: AsyncSession, user_id: int):
    """Delete user (soft delete - set is_active to False)"""
    try:
        db_user = await get_user_by_id(db, user_id)
        if not db_user:
            return False
        
        db_user.is_active = False
        await db.commit()
        logger.info(f"User deleted: {user_id}")
        return True
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting user: {e}")
        raise


async def list_users(db: AsyncSession, skip: int = 0, limit: int = 100):
    """List all active users"""
    try:
        result = await db.execute(
            select(User)
            .where(User.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise
