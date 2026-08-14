from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.comment.schemas import (
    CommentCreate,
    CommentResponse,
)
from app.comment.service import CommentService
from app.database import get_db
from app.user.auth import get_current_user
from app.user.models import User


router = APIRouter(
    prefix="/tasks/{task_id}/comments",
    tags=["comments"],
)


@router.post(
    "",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    task_id: int,
    data: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await CommentService.create(
        db,
        task_id=task_id,
        author_id=current_user.id,
        data=data,
    )


@router.get(
    "",
    response_model=list[CommentResponse],
)
async def get_comments(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await CommentService.get_by_task(
        db,
        task_id,
    )