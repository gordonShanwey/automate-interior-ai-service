"""Health check endpoints for the Interior AI Service."""

import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException

from app.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def health_check() -> Dict[str, str]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "interior-ai-service",
        "message": "Service is running"
    }


@router.get("/readiness")
async def readiness_check() -> Dict[str, Any]:
    """Readiness check including external dependencies."""
    settings = get_settings()
    health_status = {
        "status": "healthy",
        "service": "interior-ai-service",
        "checks": {}
    }
    
    # Check configuration
    try:
        # Basic configuration validation
        config_ok = all([
            settings.google_cloud_project,
            settings.smtp_username,
            settings.smtp_password,
            settings.designer_email
        ])
        health_status["checks"]["configuration"] = "healthy" if config_ok else "unhealthy"
    except Exception as e:
        logger.error(f"Configuration check failed: {e}")
        health_status["checks"]["configuration"] = f"error: {str(e)}"
    
    # Check Google Cloud Project
    try:
        project_ok = bool(settings.google_cloud_project and settings.google_cloud_project != "your-project-id")
        health_status["checks"]["google_cloud_project"] = "healthy" if project_ok else "unhealthy"
    except Exception as e:
        health_status["checks"]["google_cloud_project"] = f"error: {str(e)}"
    
    # Check Vertex AI configuration
    try:
        vertex_ok = bool(settings.vertex_ai_location and settings.genai_model)
        health_status["checks"]["vertex_ai_config"] = "healthy" if vertex_ok else "unhealthy"
    except Exception as e:
        health_status["checks"]["vertex_ai_config"] = f"error: {str(e)}"
    
    # Check Pub/Sub configuration
    try:
        pubsub_ok = bool(settings.pubsub_topic and settings.pubsub_subscription)
        health_status["checks"]["pubsub_config"] = "healthy" if pubsub_ok else "unhealthy"
    except Exception as e:
        health_status["checks"]["pubsub_config"] = f"error: {str(e)}"
    
    # Check email configuration
    try:
        email_ok = all([
            settings.smtp_server,
            settings.smtp_port,
            settings.smtp_username,
            settings.smtp_password,
            settings.designer_email
        ])
        health_status["checks"]["email_config"] = "healthy" if email_ok else "unhealthy"
    except Exception as e:
        health_status["checks"]["email_config"] = f"error: {str(e)}"
    
    # Check environment settings
    try:
        env_ok = settings.environment in ["development", "staging", "production"]
        health_status["checks"]["environment"] = "healthy" if env_ok else "unhealthy"
    except Exception as e:
        health_status["checks"]["environment"] = f"error: {str(e)}"
    
    # Overall health status
    unhealthy_checks = [k for k, v in health_status["checks"].items() if v != "healthy"]
    if unhealthy_checks:
        health_status["status"] = "unhealthy"
        health_status["unhealthy_services"] = unhealthy_checks
    
    return health_status


@router.get("/liveness")
async def liveness_check() -> Dict[str, str]:
    """Liveness check for Kubernetes health probes."""
    return {
        "status": "alive",
        "service": "interior-ai-service",
        "message": "Service is alive and responding"
    }


@router.get("/startup")
async def startup_check() -> Dict[str, str]:
    """Startup check for Kubernetes startup probes."""
    return {
        "status": "ready",
        "service": "interior-ai-service",
        "message": "Service has started successfully"
    }


@router.get("/info")
async def service_info() -> Dict[str, Any]:
    """Service information endpoint."""
    settings = get_settings()
    
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "debug": settings.debug,
        "log_level": settings.log_level,
        "google_cloud_project": settings.google_cloud_project,
        "vertex_ai_location": settings.vertex_ai_location,
        "genai_model": settings.genai_model,
        "pubsub_topic": settings.pubsub_topic,
        "pubsub_subscription": settings.pubsub_subscription,
        "smtp_server": settings.smtp_server,
        "smtp_port": settings.smtp_port,
        "designer_email": settings.designer_email,
    }
