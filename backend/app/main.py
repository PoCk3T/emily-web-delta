"""Emily Web Delta - FastAPI Application Entry Point."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.admin import router as admin_router
from app.api.analytics import router as analytics_router
from app.api.auth import router as auth_router
from app.api.checks import router as checks_router
from app.api.diffs import router as diffs_router
from app.api.health import router as health_router
from app.api.notifications import router as notifications_router
from app.api.urls import router as urls_router
from app.api.webhooks import router as webhooks_router
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup/shutdown events."""
    logger.info(f"Starting {settings.APP_NAME}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(
        f"Database URL: {'***' if 'password' in settings.DATABASE_URL else settings.DATABASE_URL}"
    )
    yield
    logger.info(f"Shutting down {settings.APP_NAME}")


app = FastAPI(
    title=settings.APP_NAME,
    description="Web page change monitoring platform with AI-powered diffing",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/v1", tags=["auth"])
app.include_router(analytics_router, prefix="/api/v1", tags=["analytics"])
app.include_router(urls_router, prefix="/api/v1", tags=["urls"])
app.include_router(checks_router, prefix="/api/v1", tags=["checks"])
app.include_router(diffs_router, prefix="/api/v1", tags=["diffs"])
app.include_router(notifications_router, prefix="/api/v1", tags=["notifications"])
app.include_router(admin_router, prefix="/api/v1", tags=["admin"])
app.include_router(webhooks_router, prefix="/api/v1", tags=["webhooks"])
app.include_router(health_router, prefix="/api/v1", tags=["health"])


@app.get("/api/v1/health")
async def health_check():
    """Root health endpoint."""
    return {"status": "ok", "app": settings.APP_NAME}


@app.get("/api/v1/ready")
async def readiness_check():
    """Readiness probe endpoint."""
    return {"ready": True}
