from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import init_db, close_db
from app.config import get_settings
from app.logger import logger
from app.user.routes import router as user_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info("Starting Task Management API")
    await init_db()
    yield
    # Shutdown
    logger.info("Shutting down Task Management API")
    await close_db()


app = FastAPI(
    title="Task Management API",
    description="REST API for task management system",
    version="1.0.0",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Include routers
app.include_router(user_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "environment": settings.ENVIRONMENT}


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to Task Management API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
