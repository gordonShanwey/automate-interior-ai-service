"""FastAPI application entry point for the Interior AI Service."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings, validate_configuration
from app.routers import health, webhooks
from app.middleware.error_handler import create_error_handler_middleware
from app.middleware.logging_middleware import create_logging_middleware
from app.utils.logging import setup_logging, StructuredLogger
from app.services.genai_service import get_genai_service
from app.services.email_service import get_email_service
from app.services.pubsub_service import get_pubsub_service

# Setup logging
setup_logging()
logger = StructuredLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("🚀 Starting Interior AI Service...")
    
    # Validate configuration on startup
    if not validate_configuration():
        logger.error("❌ Configuration validation failed during startup")
        raise RuntimeError("Configuration validation failed")
    
    logger.info("✅ Configuration validation passed")
    
    # Log startup information
    settings = get_settings()
    logger.info(f"📋 Environment: {settings.environment}")
    logger.info(f"🔧 Debug mode: {settings.debug}")
    logger.info(f"📝 Log level: {settings.log_level}")
    logger.info(f"☁️  Google Cloud Project: {settings.google_cloud_project}")
    logger.info(f"🤖 Vertex AI Location: {settings.vertex_ai_location}")
    logger.info(f"📨 Pub/Sub Topic: {settings.pubsub_topic}")
    logger.info(f"📧 Designer Email: {settings.designer_email}")
    
    # Initialize services (lazy initialization - don't fail startup)
    try:
        logger.info("🔧 Attempting to initialize services...")
        
        # Try to initialize services but don't fail if they can't connect
        try:
            genai_service = get_genai_service()
            logger.info("✅ Gen AI service initialized")
        except Exception as e:
            logger.warning(f"⚠️  Gen AI service initialization failed (will retry later): {str(e)}")
        
        try:
            email_service = get_email_service()
            logger.info("✅ Email service initialized")
        except Exception as e:
            logger.warning(f"⚠️  Email service initialization failed (will retry later): {str(e)}")
        
        try:
            pubsub_service = get_pubsub_service()
            logger.info("✅ Pub/Sub service initialized")
        except Exception as e:
            logger.warning(f"⚠️  Pub/Sub service initialization failed (will retry later): {str(e)}")
        
        logger.info("✅ Service initialization completed (some services may retry later)")
        
    except Exception as e:
        logger.error(f"❌ Critical service initialization failed: {str(e)}")
        # Don't raise here - let the app start and services can retry later
    
    logger.info("✅ Interior AI Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Interior AI Service...")
    
    # Cleanup services if needed
    try:
        # Add any cleanup logic here
        logger.info("🧹 Service cleanup completed")
    except Exception as e:
        logger.error(f"❌ Service cleanup failed: {str(e)}")
    
    logger.info("✅ Interior AI Service shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    
    # Create FastAPI app with lifespan context manager
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Interior designer automation service using Google Gen AI",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=lifespan,
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add logging middleware
    app.add_middleware(create_logging_middleware(
        log_requests=True,
        log_responses=True
    ))
    
    # Add error handling middleware
    app.add_middleware(create_error_handler_middleware(
        include_details=settings.debug
    ))
    
    # Add global exception handler for unhandled errors
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler for unhandled errors."""
        logger.error(f"❌ Unhandled exception: {exc}", exc_info=True)
        
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "timestamp": "2024-01-15T10:30:00Z"
                }
            }
        )
    
    # Include routers
    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(webhooks.router, tags=["webhooks"])
    
    # Root endpoint
    @app.get("/", tags=["root"])
    async def root():
        """Root endpoint with service information."""
        settings = get_settings()
        return {
            "service": settings.app_name,
            "version": settings.app_version,
            "status": "running",
            "environment": settings.environment,
            "docs": "/docs" if settings.debug else None,
            "health": "/health",
            "webhooks": "/webhooks"
        }
    
    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
