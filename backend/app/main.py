"""Swaarm API — FastAPI application entry point."""

from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.simulation import router as simulation_router
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
    docs_url="/api/docs" if settings.debug else None,  # Disable Swagger in production
    redoc_url=None,
)


# Global exception handler — never leak internal errors to client
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch all unhandled exceptions. Log details, return generic error."""
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc!s}")
    if settings.sentry_dsn:
        sentry_sdk.capture_exception(exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Ein interner Fehler ist aufgetreten. Bitte versuche es später erneut."},
    )


# CORS — restrict in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Routers
app.include_router(health_router, prefix="/api", tags=["health"])
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(simulation_router, prefix="/api/simulation", tags=["simulation"])
