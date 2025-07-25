"""Health check endpoints for the Interior AI Service."""

import logging
from typing import Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.utils.auth import run_authentication_tests, get_authentication_help
from app.utils.logging import log_service_health, StructuredLogger
from app.services.genai_service import get_genai_service
from app.services.email_service import get_email_service
from app.services.pubsub_service import get_pubsub_service

logger = StructuredLogger("health")
router = APIRouter()


@router.get("/")
async def health_check() -> Dict[str, str]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "interior-ai-service",
        "message": "Service is running",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/readiness")
async def readiness_check() -> Dict[str, Any]:
    """Readiness check including external dependencies."""
    settings = get_settings()
    health_status = {
        "status": "healthy",
        "service": "interior-ai-service",
        "timestamp": datetime.utcnow().isoformat(),
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
        log_service_health("configuration", "healthy" if config_ok else "unhealthy")
    except Exception as e:
        logger.error(f"Configuration check failed: {e}")
        health_status["checks"]["configuration"] = f"error: {str(e)}"
        log_service_health("configuration", "error", {"error": str(e)})
    
    # Check Google Cloud Project
    try:
        project_ok = bool(settings.google_cloud_project and settings.google_cloud_project != "your-project-id")
        health_status["checks"]["google_cloud_project"] = "healthy" if project_ok else "unhealthy"
        log_service_health("google_cloud_project", "healthy" if project_ok else "unhealthy")
    except Exception as e:
        health_status["checks"]["google_cloud_project"] = f"error: {str(e)}"
        log_service_health("google_cloud_project", "error", {"error": str(e)})
    
    # Check Vertex AI configuration
    try:
        vertex_ok = bool(settings.vertex_ai_location and settings.genai_model)
        health_status["checks"]["vertex_ai_config"] = "healthy" if vertex_ok else "unhealthy"
        log_service_health("vertex_ai_config", "healthy" if vertex_ok else "unhealthy")
    except Exception as e:
        health_status["checks"]["vertex_ai_config"] = f"error: {str(e)}"
        log_service_health("vertex_ai_config", "error", {"error": str(e)})
    
    # Check Pub/Sub configuration
    try:
        pubsub_ok = bool(settings.pubsub_topic and settings.pubsub_subscription)
        health_status["checks"]["pubsub_config"] = "healthy" if pubsub_ok else "unhealthy"
        log_service_health("pubsub_config", "healthy" if pubsub_ok else "unhealthy")
    except Exception as e:
        health_status["checks"]["pubsub_config"] = f"error: {str(e)}"
        log_service_health("pubsub_config", "error", {"error": str(e)})
    
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
        log_service_health("email_config", "healthy" if email_ok else "unhealthy")
    except Exception as e:
        health_status["checks"]["email_config"] = f"error: {str(e)}"
        log_service_health("email_config", "error", {"error": str(e)})
    
    # Check environment settings
    try:
        env_ok = settings.environment in ["development", "staging", "production"]
        health_status["checks"]["environment"] = "healthy" if env_ok else "unhealthy"
        log_service_health("environment", "healthy" if env_ok else "unhealthy")
    except Exception as e:
        health_status["checks"]["environment"] = f"error: {str(e)}"
        log_service_health("environment", "error", {"error": str(e)})
    
    # Check Google Cloud authentication
    try:
        auth_results = await run_authentication_tests()
        if auth_results["overall_status"] == "healthy":
            health_status["checks"]["google_cloud_auth"] = "healthy"
        elif auth_results["overall_status"] == "partial":
            health_status["checks"]["google_cloud_auth"] = "partial"
        else:
            health_status["checks"]["google_cloud_auth"] = "unhealthy"
        
        # Add detailed auth results
        health_status["auth_details"] = auth_results
        log_service_health("google_cloud_auth", auth_results["overall_status"], auth_results)
        
    except Exception as e:
        health_status["checks"]["google_cloud_auth"] = f"error: {str(e)}"
        log_service_health("google_cloud_auth", "error", {"error": str(e)})
    
    # Check Google Gen AI connectivity
    try:
        genai_service = get_genai_service()
        genai_test = genai_service.test_connection()
        health_status["checks"]["genai_service"] = genai_test["status"]
        health_status["genai_details"] = genai_test
        log_service_health("genai_service", genai_test["status"], genai_test)
    except Exception as e:
        health_status["checks"]["genai_service"] = f"error: {str(e)}"
        log_service_health("genai_service", "error", {"error": str(e)})
    
    # Check email service connectivity
    try:
        email_service = get_email_service()
        email_test = email_service.test_connection()
        health_status["checks"]["email_service"] = email_test["status"]
        health_status["email_details"] = email_test
        log_service_health("email_service", email_test["status"], email_test)
    except Exception as e:
        health_status["checks"]["email_service"] = f"error: {str(e)}"
        log_service_health("email_service", "error", {"error": str(e)})
    
    # Check Pub/Sub service connectivity
    try:
        pubsub_service = get_pubsub_service()
        pubsub_test = pubsub_service.test_connection()
        health_status["checks"]["pubsub_service"] = pubsub_test["status"]
        health_status["pubsub_details"] = pubsub_test
        log_service_health("pubsub_service", pubsub_test["status"], pubsub_test)
    except Exception as e:
        health_status["checks"]["pubsub_service"] = f"error: {str(e)}"
        log_service_health("pubsub_service", "error", {"error": str(e)})
    
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
        "message": "Service is alive and responding",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/startup")
async def startup_check() -> Dict[str, str]:
    """Startup check for Kubernetes startup probes."""
    return {
        "status": "ready",
        "service": "interior-ai-service",
        "message": "Service has started successfully",
        "timestamp": datetime.utcnow().isoformat()
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
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/auth-help")
async def authentication_help() -> Dict[str, str]:
    """Get authentication setup help."""
    return {
        "help": get_authentication_help(),
        "endpoint": "/health/auth-help",
        "description": "Authentication setup instructions",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/services")
async def service_status() -> Dict[str, Any]:
    """Detailed service status endpoint."""
    services_status = {
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    # Gen AI Service Status
    try:
        genai_service = get_genai_service()
        genai_test = genai_service.test_connection()
        services_status["services"]["genai"] = genai_test
    except Exception as e:
        services_status["services"]["genai"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Email Service Status
    try:
        email_service = get_email_service()
        email_test = email_service.test_connection()
        services_status["services"]["email"] = email_test
    except Exception as e:
        services_status["services"]["email"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Pub/Sub Service Status
    try:
        pubsub_service = get_pubsub_service()
        pubsub_test = pubsub_service.test_connection()
        services_status["services"]["pubsub"] = pubsub_test
    except Exception as e:
        services_status["services"]["pubsub"] = {
            "status": "error",
            "error": str(e)
        }
    
    return services_status
