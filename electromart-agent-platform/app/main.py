"""
Main FastAPI application for ElectroMart Multi-Agent System
Production-ready with professional middleware stack
"""
from dotenv import load_dotenv
load_dotenv()  # loads .env into os.environ

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.api.routes import router
from app.api.health import router as health_router
from app.api.demo import router as demo_router
from app.api.socketio_handler import socket_app, sio
from app.api.middleware import (
    RequestIDMiddleware,
    RequestLoggingMiddleware,
    CORSSecurityMiddleware,
    RateLimitMiddleware,
    configure_exception_handlers
)
from app.database.connection import init_db
from app.utils.config import settings
from app.utils.logger import logger
from app.core.constants import RateLimiting, MessageProcessing

# Create FastAPI app with enhanced configuration
app = FastAPI(
    title="ElectroMart Multi-Agent System",
    description="Production-ready intelligent multi-agent system for customer support with LangGraph",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={
        "name": "ElectroMart Support",
        "email": "support@electromart.com"
    },
    license_info={
        "name": "MIT License"
    }
)

# ============================================================================
# Middleware Stack (Order matters!)
# ============================================================================

# 1. CORS - Must be first
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Security headers
app.add_middleware(CORSSecurityMiddleware)

# 3. Rate limiting
app.add_middleware(
    RateLimitMiddleware,
    max_requests=RateLimiting.MAX_REQUESTS_PER_WINDOW,
    window_seconds=RateLimiting.RATE_LIMIT_WINDOW_SECONDS
)

# 4. Request logging
app.add_middleware(RequestLoggingMiddleware)

# 5. Request ID tracking
app.add_middleware(RequestIDMiddleware)

# ============================================================================
# Exception Handlers
# ============================================================================

configure_exception_handlers(app)

# ============================================================================
# Routes
# ============================================================================

# Include REST API routes
app.include_router(router, prefix="/api", tags=["API"])

# Include health and monitoring routes (no prefix for standard /health)
app.include_router(health_router, tags=["Health & Monitoring"])

# Include demo dashboard routes (for showcasing database operations)
app.include_router(demo_router, tags=["Demo Dashboard"])

# Mount Socket.IO
app.mount("/", socket_app)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("=" * 60)
    logger.info("Starting ElectroMart Multi-Agent System v1.0.0")
    logger.info("=" * 60)

    try:
        # Initialize database
        init_db()
        logger.info("✓ Database initialized")

        # Initialize Redis session manager
        from .utils.redis_session import get_session_manager
        session_manager = await get_session_manager()
        if session_manager.redis_client:
            logger.info("✓ Redis session manager connected")
        else:
            logger.warning("⚠ Redis unavailable - using in-memory session storage")

        # Initialize analytics
        from .utils.analytics import get_analytics
        analytics = await get_analytics()
        if analytics.redis_client:
            logger.info("✓ Performance analytics enabled")
        else:
            logger.warning("⚠ Analytics unavailable - metrics will not be persisted")

        # Initialize handoff manager
        from .utils.human_handoff import get_handoff_manager
        handoff_manager = await get_handoff_manager()
        if handoff_manager.redis_client:
            logger.info("✓ Human handoff queue initialized")
        else:
            logger.warning("⚠ Handoff queue unavailable - escalations will not be queued")

        # Initialize concurrent message queue manager
        from .api.socketio_handler import initialize_queue_manager
        await initialize_queue_manager(num_workers=MessageProcessing.NUM_WORKERS)
        logger.info(f"✓ Concurrent message queue initialized ({MessageProcessing.NUM_WORKERS} workers)")

        # Log configuration
        logger.info("-" * 60)
        logger.info("Configuration:")
        logger.info(f"  Environment: {settings.environment}")
        logger.info(f"  OpenAI Model: {settings.openai_model}")
        logger.info(f"  LangSmith Tracing: {settings.langchain_tracing_v2}")
        logger.info(f"  Redis URL: {settings.redis_url}")
        logger.info(f"  CORS Origins: {', '.join(settings.cors_origins_list)}")
        logger.info("-" * 60)

        logger.info("Features Enabled:")
        logger.info("  ✓ Multi-Agent Workflow (LangGraph)")
        logger.info("  ✓ Real-time Communication (Socket.IO)")
        logger.info("  ✓ Concurrent Message Processing")
        logger.info("  ✓ Persistent Sessions (Redis)")
        logger.info("  ✓ Performance Analytics")
        logger.info("  ✓ Sentiment Analysis (TextBlob)")
        logger.info("  ✓ Human Handoff Capability")
        logger.info("  ✓ Rate Limiting & Security")
        logger.info("-" * 60)

        logger.info("API Documentation: http://localhost:8000/docs")
        logger.info("Health Check: http://localhost:8000/health")
        logger.info("Metrics: http://localhost:8000/metrics")
        logger.info("=" * 60)
        logger.info("✓ ElectroMart Multi-Agent System started successfully")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"✗ Failed to start application: {str(e)}", exc_info=True)
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("=" * 60)
    logger.info("Shutting down ElectroMart Multi-Agent System...")
    logger.info("=" * 60)

    try:
        # Close message queue manager
        from .utils.message_queue import shutdown_queue_manager

        await shutdown_queue_manager()
        logger.info("✓ Message queue manager stopped")

        # Close Redis connections
        from .utils.redis_session import close_session_manager
        from .utils.analytics import close_analytics
        from .utils.human_handoff import close_handoff_manager

        await close_session_manager()
        logger.info("✓ Session manager closed")

        await close_analytics()
        logger.info("✓ Analytics closed")

        await close_handoff_manager()
        logger.info("✓ Handoff manager closed")

        logger.info("=" * 60)
        logger.info("✓ Shutdown complete")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}", exc_info=True)


@app.get("/")
async def root():
    """
    Root endpoint with service information

    Returns basic information about the service and available endpoints.
    """
    return {
        "service": "ElectroMart Multi-Agent System",
        "version": "1.0.0",
        "status": "running",
        "description": "Production-ready multi-agent system for customer support",
        "features": [
            "Multi-Agent Workflow (LangGraph)",
            "Real-time Communication (Socket.IO)",
            "Concurrent Message Processing",
            "Persistent Sessions",
            "Performance Analytics",
            "Sentiment Analysis",
            "Human Handoff"
        ],
        "endpoints": {
            "api": "/api",
            "docs": "/docs",
            "health": "/health",
            "metrics": "/metrics",
            "analytics": "/analytics/agents",
            "socket_io": "/socket.io"
        },
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_json": "/openapi.json"
        }
    }


def main():
    """Run the application"""
    uvicorn.run(
        "app.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    main()
