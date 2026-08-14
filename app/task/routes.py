from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.task.schemas import (
    TaskCreate,
    TaskResponse,
    TaskStatusUpdate,
    TaskUpdate,
)
from app.task.service import TaskService
from app.user.auth import get_current_user
from app.user.models import User

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
)


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
        data: TaskCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    return await TaskService.create(
        db,
        data,
        author_id=current_user.id,
    )


@router.get(
    "",
    response_model=list[TaskResponse],
)
async def get_tasks(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    return await TaskService.get_all(db)


@router.patch(
    "/{task_id}/status",
    response_model=TaskResponse,
)
async def change_task_status(
        task_id: int,
        data: TaskStatusUpdate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    return await TaskService.change_status(
        db,
        task_id,
        data,
    )


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
)
async def get_task(
        task_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    return await TaskService.get_by_id(
        db,
        task_id,
    )


@router.put(
    "/{task_id}",
    response_model=TaskResponse,
)
async def update_task(
        task_id: int,
        data: TaskUpdate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    return await TaskService.update(
        db,
        task_id,
        data,
    )


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_task(
        task_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    await TaskService.delete(
        db,
        task_id,
    )
