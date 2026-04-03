"""Swaarm API — FastAPI application entry point."""

from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.health import router as health_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    logger.info("Swaarm API starting up")

    # Initialize Sentry if DSN is configured
    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            traces_sample_rate=0.1,
            environment="production" if not settings.debug else "development",
        )
        logger.info("Sentry initialized")

    yield

    logger.info("Swaarm API shutting down")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Pre-Testing Platform for Strategic Communications",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health_router, prefix="/api", tags=["health"])
