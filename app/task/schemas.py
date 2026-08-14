from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field
from app.task.models import TaskPriority, TaskStatus
from enum import Enum


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
    model_config = ConfigDict(
        from_attributes=True,
    )

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


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class TaskSortField(str, Enum):
    DEFAULT = "default"
    CREATED_AT = "created_at"
    DEADLINE = "deadline"
    PRIORITY = "priority"


class TaskFilter(BaseModel):
    search: str | None = None

    status: TaskStatus | None = None

    priority: TaskPriority | None = None

    assignee_id: int | None = Field(
        default=None,
        gt=0,
    )

    deadline_from: datetime | None = None

    deadline_to: datetime | None = None

    sort_by: TaskSortField = TaskSortField.DEFAULT

    sort_order: SortOrder = SortOrder.ASC

    page: int = Field(
        default=1,
        ge=1,
    )

    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
    )


class TaskListResponse(BaseModel):
    items: list[TaskResponse]

    total: int

    page: int

    page_size: int

    pages: int


class TaskStatisticsResponse(BaseModel):
    total: int

    by_status: dict[TaskStatus, int]

    by_priority: dict[TaskPriority, int]

    overdue: int

    active: int
