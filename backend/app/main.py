"""
RecoverAI — Autonomous Revenue Recovery Agent Main FastAPI Server
Buildathon Track 3: AI Revenue Recovery
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import get_settings
from backend.app.core.logging import setup_structured_logging, redact_secrets
from backend.app.core.metrics import metrics
from backend.app.api.middleware import CorrelationIdMiddleware
from backend.app.api.webhooks import router as webhooks_router
from backend.app.api.health import router as health_router
from backend.app.db.database import init_db

settings = get_settings()

# Initialize Structured Redacting Logging
setup_structured_logging(logging.INFO)
logger = logging.getLogger("recoverai.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on application startup
    await init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Autonomous Revenue Recovery Agent for Razorpay AI Buildathon Track 3",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure Correlation ID & CORS Middleware
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.app.api.demo import router as demo_router

# Include Routers
app.include_router(health_router)
app.include_router(webhooks_router)
app.include_router(demo_router)
app.include_router(demo_router, prefix="/api/v1")


# Global Security-Safe Exception Handler (No raw stack traces or secret leakage in HTTP response)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_msg = redact_secrets(str(exc))
    logger.error(f"Unhandled Exception on {request.method} {request.url.path}: {error_msg}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An error occurred while processing the request. Technical details have been logged securely.",
            "path": request.url.path
        }
    )


@app.get("/", tags=["System"])
async def root():
    return {
        "status": "online",
        "service": settings.APP_NAME,
        "version": "1.0.0",
        "environment": settings.APP_ENV,
        "docs": "/docs",
    }


@app.get("/metrics", tags=["System"])
async def get_metrics():
    """
    Operational diagnostic metrics endpoint.
    Exposes safe event counters without secret exposure.
    """
    return {
        "service": settings.APP_NAME,
        "metrics": metrics.get_metrics()
    }
