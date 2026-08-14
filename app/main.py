from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.user.routes import router as user_router
from app.task.routes import router as task_router


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


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