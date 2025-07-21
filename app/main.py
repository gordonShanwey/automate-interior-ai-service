"""FastAPI application entry point for the Interior AI Service."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings, validate_configuration
from app.routers import health, webhooks

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


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
    
    logger.info("✅ Interior AI Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Interior AI Service...")
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
    
    # Add request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log incoming requests and responses."""
        logger.info(f"📥 {request.method} {request.url.path}")
        
        response = await call_next(request)
        
        logger.info(f"📤 {request.method} {request.url.path} - {response.status_code}")
        return response
    
    # Add global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler for unhandled errors."""
        logger.error(f"❌ Unhandled exception: {exc}", exc_info=True)
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": "An unexpected error occurred",
                "request_id": getattr(request.state, "request_id", "unknown"),
            },
        )
    
    # Include routers
    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
    
    # Root endpoint
    @app.get("/", tags=["root"])
    async def root():
        """Root endpoint with service information."""
        return {
            "service": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "status": "running",
            "docs": "/docs" if settings.debug else "disabled in production",
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
