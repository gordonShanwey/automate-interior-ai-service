"""Global error handling middleware for the Interior AI Service."""

import time
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.errors import InteriorAIServiceError, format_error_response
from app.utils.logging import StructuredLogger

logger = StructuredLogger("error_handler")


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware."""
    
    def __init__(self, app, include_details: bool = False):
        super().__init__(app)
        self.include_details = include_details
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and handle errors."""
        start_time = time.time()
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Log successful requests (optional)
            duration = time.time() - start_time
            if duration > 1.0:  # Log slow requests
                logger.warning(
                    f"🐌 Slow request detected",
                    path=request.url.path,
                    method=request.method,
                    duration_seconds=duration
                )
            
            return response
            
        except InteriorAIServiceError as e:
            # Handle our custom errors
            duration = time.time() - start_time
            logger.error(
                f"❌ Service error: {e.error_code}",
                path=request.url.path,
                method=request.method,
                error_code=e.error_code,
                error_message=e.message,
                duration_seconds=duration,
                details=e.details
            )
            
            # Format error response
            error_response = format_error_response(e, self.include_details)
            return JSONResponse(
                status_code=500,
                content=error_response
            )
            
        except Exception as e:
            # Handle unexpected errors
            duration = time.time() - start_time
            logger.error(
                f"❌ Unexpected error: {str(e)}",
                path=request.url.path,
                method=request.method,
                duration_seconds=duration,
                error_type=type(e).__name__
            )
            
            # Format generic error response
            error_response = format_error_response(e, self.include_details)
            return JSONResponse(
                status_code=500,
                content=error_response
            )


def create_error_handler_middleware(include_details: bool = False) -> ErrorHandlerMiddleware:
    """Create error handler middleware instance."""
    return lambda app: ErrorHandlerMiddleware(app, include_details)
