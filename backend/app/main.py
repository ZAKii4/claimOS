"""
claimOS — Application Entry Point.

FastAPI application factory with middleware, exception handlers,
and OpenAPI metadata.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import router as api_router
from app.config.settings import get_settings
from app.core.logging import get_logger, setup_logging
from app.utils.exceptions import (
    BusinessValidationError,
    ClaimOSException,
    DuplicateEntityError,
    EngineProcessingError,
    EntityNotFoundError,
)

settings = get_settings()
logger = get_logger("claimOS.main")


# ── Lifespan ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    setup_logging()
    logger.info("claimOS %s starting (%s)", settings.APP_VERSION, settings.ENVIRONMENT)
    yield
    logger.info("claimOS shutting down.")


# ── Application ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="claimOS API",
    description=(
        "Intelligent Claims Processing Platform — "
        "AI-powered document analysis, extraction, and decision engine "
        "for insurance claim management."
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middleware ────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ───────────────────────────────────────────────────────────────────

from app.review.review_router import router as review_router

app.include_router(api_router)
app.include_router(review_router)


# ── Exception Handlers ───────────────────────────────────────────────────────

@app.exception_handler(EntityNotFoundError)
async def entity_not_found_handler(request: Request, exc: EntityNotFoundError):
    return JSONResponse(status_code=404, content={"detail": exc.detail})


@app.exception_handler(DuplicateEntityError)
async def duplicate_entity_handler(request: Request, exc: DuplicateEntityError):
    return JSONResponse(status_code=409, content={"detail": exc.detail})


@app.exception_handler(BusinessValidationError)
async def business_validation_handler(request: Request, exc: BusinessValidationError):
    return JSONResponse(status_code=422, content={"detail": exc.detail})


@app.exception_handler(EngineProcessingError)
async def engine_processing_handler(request: Request, exc: EngineProcessingError):
    return JSONResponse(status_code=502, content={"detail": exc.detail})


@app.exception_handler(ClaimOSException)
async def generic_claimsOS_handler(request: Request, exc: ClaimOSException):
    return JSONResponse(status_code=500, content={"detail": exc.detail})
