from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.task.models import TaskPriority, TaskStatus


class TaskBase(BaseModel):
    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    description: str | None = None

    priority: TaskPriority = TaskPriority.MEDIUM

    assignee_id: int | None = Field(
        default=None,
        gt=0,
    )

    deadline: datetime


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    description: str | None = None

    priority: TaskPriority | None = None

    assignee_id: int | None = Field(
        default=None,
        gt=0,
    )

    deadline: datetime | None = None

class TaskStatusUpdate(BaseModel):
    status: TaskStatus

class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    assignee_id: int | None
    author_id: int
    deadline: datetime
    created_at: datetime
    updated_at: datetime

