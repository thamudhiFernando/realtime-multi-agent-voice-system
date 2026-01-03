"""
Comprehensive Health Check and Metrics Endpoints
Production-ready monitoring and observability
"""
from fastapi import APIRouter, Depends
from typing import Dict, Any
import time
import psutil
import sys
from datetime import datetime
from ..schemas.schemas import HealthCheckResponse, ServiceHealth, MetricsResponse, MetricSample
from ..utils.config import settings
from ..utils.logger import logger

router = APIRouter(tags=["Health & Monitoring"])

# Application version
APP_VERSION = "1.0.0"

# Application start time
APP_START_TIME = time.time()


@router.get("/health", response_model=HealthCheckResponse)
async def comprehensive_health_check() -> HealthCheckResponse:
    """
    Comprehensive health check endpoint

    Checks:
    - Redis connection
    - Database connection (if configured)
    - OpenAI API configuration
    - System resources
    - Feature availability

    Returns:
        HealthCheckResponse with detailed service status
    """
    services = {}

    # Check Redis
    services["redis"] = await _check_redis()

    # Check Database
    services["database"] = await _check_database()

    # Check OpenAI
    services["openai"] = _check_openai_config()

    # Check System Resources
    services["system"] = _check_system_resources()

    # Determine overall status
    overall_status = _determine_overall_status(services)

    # Check feature availability
    features = {
        "persistent_sessions": services["redis"]["status"] == "healthy",
        "analytics": services["redis"]["status"] == "healthy",
        "sentiment_analysis": True,  # TextBlob is always available after install
        "human_handoff": services["redis"]["status"] == "healthy",
        "database_operations": services["database"]["status"] in ["healthy", "not_configured"],
        "multi_agent_workflow": services["openai"]["status"] == "healthy"
    }

    return HealthCheckResponse(
        status=overall_status,
        version=APP_VERSION,
        services=services,
        features=features
    )


@router.get("/health/live")
async def liveness_probe() -> Dict[str, str]:
    """
    Kubernetes liveness probe endpoint

    Simple check to verify the application is running
    Returns 200 if alive, used by orchestrators to restart unhealthy pods
    """
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness_probe() -> Dict[str, Any]:
    """
    Kubernetes readiness probe endpoint

    Checks if application is ready to serve traffic
    Returns 200 if ready, 503 if not ready
    """
    # Check critical dependencies
    redis_status = await _check_redis()
    openai_status = _check_openai_config()

    is_ready = (
        redis_status["status"] in ["healthy", "degraded"] and
        openai_status["status"] == "healthy"
    )

    if is_ready:
        return {
            "status": "ready",
            "redis": redis_status["status"],
            "openai": openai_status["status"]
        }
    else:
        from fastapi import HTTPException, status as http_status
        raise HTTPException(
            status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not ready"
        )


@router.get("/metrics", response_model=MetricsResponse)
async def prometheus_metrics() -> MetricsResponse:
    """
    Prometheus-compatible metrics endpoint

    Provides:
    - Application metrics
    - System metrics
    - Business metrics
    - Performance metrics

    Note: For production, consider using prometheus_client library
    """
    metrics = []

    # Application info
    metrics.append(MetricSample(
        name="app_info",
        value=1,
        labels={"version": APP_VERSION, "python_version": sys.version.split()[0]}
    ))

    # Uptime
    uptime_seconds = time.time() - APP_START_TIME
    metrics.append(MetricSample(
        name="app_uptime_seconds",
        value=uptime_seconds
    ))

    # System metrics
    cpu_percent = psutil.cpu_percent(interval=0.1)
    metrics.append(MetricSample(
        name="system_cpu_usage_percent",
        value=cpu_percent
    ))

    memory = psutil.virtual_memory()
    metrics.append(MetricSample(
        name="system_memory_usage_percent",
        value=memory.percent
    ))

    metrics.append(MetricSample(
        name="system_memory_available_bytes",
        value=memory.available
    ))

    # Process metrics
    process = psutil.Process()
    process_memory = process.memory_info()
    metrics.append(MetricSample(
        name="process_memory_rss_bytes",
        value=process_memory.rss
    ))

    metrics.append(MetricSample(
        name="process_cpu_percent",
        value=process.cpu_percent(interval=0.1)
    ))

    # Redis metrics (if available)
    try:
        from ..utils.redis_session import get_session_manager
        session_manager = await get_session_manager()
        if session_manager.redis_client:
            active_sessions = await session_manager.get_active_sessions_count()
            metrics.append(MetricSample(
                name="redis_active_sessions",
                value=active_sessions
            ))
    except Exception as e:
        logger.debug(f"Could not fetch Redis metrics: {e}")

    # Analytics metrics (if available)
    try:
        from ..utils.analytics import get_analytics
        analytics = await get_analytics()

        agent_names = ["orchestrator", "sales", "marketing", "support", "logistics"]
        for agent_name in agent_names:
            stats = await analytics.get_agent_stats(agent_name)
            if stats and stats.get("total_requests", 0) > 0:
                metrics.append(MetricSample(
                    name="agent_requests_total",
                    value=stats["total_requests"],
                    labels={"agent": agent_name}
                ))

                metrics.append(MetricSample(
                    name="agent_success_rate",
                    value=stats["success_rate"],
                    labels={"agent": agent_name}
                ))

                metrics.append(MetricSample(
                    name="agent_avg_response_time_ms",
                    value=stats["avg_response_time_ms"],
                    labels={"agent": agent_name}
                ))
    except Exception as e:
        logger.debug(f"Could not fetch analytics metrics: {e}")

    return MetricsResponse(metrics=metrics)


@router.get("/info")
async def application_info() -> Dict[str, Any]:
    """
    Application information endpoint

    Returns:
        Application metadata, version, configuration (non-sensitive)
    """
    uptime_seconds = time.time() - APP_START_TIME

    return {
        "application": "ElectroMart Multi-Agent System",
        "version": APP_VERSION,
        "environment": settings.environment,
        "uptime_seconds": round(uptime_seconds, 2),
        "started_at": datetime.fromtimestamp(APP_START_TIME).isoformat(),
        "python_version": sys.version.split()[0],
        "features": {
            "langgraph": True,
            "openai_gpt4": True,
            "socketio": True,
            "redis_sessions": True,
            "sentiment_analysis": True,
            "performance_analytics": True,
            "human_handoff": True
        },
        "endpoints": {
            "api": "/api",
            "docs": "/docs",
            "health": "/health",
            "metrics": "/metrics"
        }
    }


# ============================================================================
# Helper Functions
# ============================================================================

async def _check_redis() -> ServiceHealth:
    """Check Redis connection status"""
    try:
        from ..utils.redis_session import get_session_manager
        start_time = time.time()

        session_manager = await get_session_manager()

        if session_manager.redis_client:
            # Test Redis connection with ping
            await session_manager.redis_client.ping()

            latency_ms = (time.time() - start_time) * 1000

            return ServiceHealth(
                status="healthy",
                latency_ms=round(latency_ms, 2),
                details={"connected": True}
            )
        else:
            return ServiceHealth(
                status="degraded",
                details={"connected": False, "message": "Using in-memory fallback"}
            )

    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
        return ServiceHealth(
            status="unhealthy",
            details={"error": str(e), "message": "Redis unavailable"}
        )


async def _check_database() -> ServiceHealth:
    """Check database connection status"""
    if not settings.database_url or "postgresql" not in settings.database_url:
        return ServiceHealth(
            status="not_configured",
            details={"message": "Database not configured, using knowledge base"}
        )

    try:
        from ..database.connection import SessionLocal
        start_time = time.time()

        # Test database connection
        db = SessionLocal()
        try:
            # Simple query to test connection
            db.execute("SELECT 1")
            latency_ms = (time.time() - start_time) * 1000

            return ServiceHealth(
                status="healthy",
                latency_ms=round(latency_ms, 2),
                details={"connected": True}
            )
        finally:
            db.close()

    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        return ServiceHealth(
            status="unhealthy",
            details={"error": str(e), "message": "Database unavailable"}
        )


def _check_openai_config() -> ServiceHealth:
    """Check OpenAI API configuration"""
    if not settings.openai_api_key or settings.openai_api_key == "":
        return ServiceHealth(
            status="unhealthy",
            details={"error": "OpenAI API key not configured"}
        )

    return ServiceHealth(
        status="healthy",
        details={
            "configured": True,
            "model": settings.openai_model
        }
    )


def _check_system_resources() -> ServiceHealth:
    """Check system resource availability"""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()

        # Determine status based on resource usage
        if cpu_percent > 90 or memory.percent > 90:
            status = "degraded"
        elif cpu_percent > 95 or memory.percent > 95:
            status = "unhealthy"
        else:
            status = "healthy"

        return ServiceHealth(
            status=status,
            details={
                "cpu_percent": round(cpu_percent, 2),
                "memory_percent": round(memory.percent, 2),
                "memory_available_gb": round(memory.available / (1024**3), 2)
            }
        )

    except Exception as e:
        logger.warning(f"System resource check failed: {e}")
        return ServiceHealth(
            status="unknown",
            details={"error": str(e)}
        )


def _determine_overall_status(services: Dict[str, ServiceHealth]) -> str:
    """Determine overall system status from service health"""
    statuses = [service.status for service in services.values()]

    if "unhealthy" in statuses:
        # Check if critical services are unhealthy
        if services.get("openai", {}).get("status") == "unhealthy":
            return "unhealthy"
        # Redis unhealthy is degraded (fallback available)
        return "degraded"

    if "degraded" in statuses:
        return "degraded"

    return "healthy"
