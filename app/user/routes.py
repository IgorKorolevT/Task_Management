from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.user import schemas, crud, auth
from app.logger import logger
from datetime import timedelta

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    """Register new user"""
    try:
        # Check if user exists
        existing_user = await crud.get_user_by_username(db, user.username)
        if existing_user:
            logger.warning(f"Registration failed: username {user.username} already exists")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        existing_email = await crud.get_user_by_email(db, user.email)
        if existing_email:
            logger.warning(f"Registration failed: email {user.email} already exists")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        db_user = await crud.create_user(db, user)
        return db_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/login", response_model=schemas.TokenResponse)
async def login(credentials: schemas.UserLogin, db: AsyncSession = Depends(get_db)):
    """Login user and return access/refresh tokens"""
    try:
        user = await crud.authenticate_user(db, credentials.username, credentials.password)
        if not user:
            logger.warning(f"Login failed: invalid credentials for {credentials.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        access_token = auth.create_access_token(data={"sub": user.username, "user_id": user.id})
        refresh_token = auth.create_refresh_token(data={"sub": user.username, "user_id": user.id})
        
        logger.info(f"User logged in: {user.username}")
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/refresh", response_model=schemas.TokenRefreshResponse)
async def refresh_token(request: schemas.TokenRefreshRequest):
    """Refresh access token using refresh token"""
    try:
        payload = auth.decode_token(request.refresh_token)
        
        if payload.get("type") != "refresh":
            logger.warning("Refresh token validation failed: not a refresh token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        username = payload.get("sub")
        user_id = payload.get("user_id")
        
        if not username or not user_id:
            logger.warning("Refresh token validation failed: missing claims")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        access_token = auth.create_access_token(data={"sub": username, "user_id": user_id})
        
        logger.info(f"Token refreshed for user: {username}")
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.get("/me", response_model=schemas.UserResponse)
async def get_current_user(token: str = None, db: AsyncSession = Depends(get_db)):
    """Get current user info"""
    try:
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        payload = auth.decode_token(token)
        user_id = payload.get("user_id")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        user = await crud.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


@router.get("/{user_id}", response_model=schemas.UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """Get user by ID"""
    try:
        user = await crud.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put("/{user_id}", response_model=schemas.UserResponse)
async def update_user(user_id: int, user_update: schemas.UserUpdate, db: AsyncSession = Depends(get_db)):
    """Update user"""
    try:
        user = await crud.update_user(db, user_id, user_update)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """Delete user (soft delete)"""
    try:
        success = await crud.delete_user(db, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
