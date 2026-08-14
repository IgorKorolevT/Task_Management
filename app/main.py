from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.user.routes import router as user_router
from app.task.routes import router as task_router
from app.comment.router import router as comment_router
from app.database import async_session_maker
from app.task.background import overdue_tasks_worker
import asyncio

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):

    worker_task = asyncio.create_task(
        overdue_tasks_worker(
            async_session_maker,
            interval=settings.OVERDUE_TASK_CHECK_INTERVAL,
        )
    )

    try:
        yield

    finally:
        worker_task.cancel()

        try:
            await worker_task
        except asyncio.CancelledError:
            pass




app = FastAPI(
    title="Task Management API",
    description="REST API for task management system",
    version="1.0.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
)


app.include_router(
    user_router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    task_router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    comment_router,
    prefix=settings.API_V1_PREFIX,
)


@app.get(
    "/",
    tags=["health"],
)
async def root():
    return {
        "message": "Task Management API",
        "status": "ok",
    }


@app.get(
    "/health",
    tags=["health"],
)
async def health():
    return {
        "status": "ok",
    }