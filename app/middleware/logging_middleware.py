"""Request/response logging middleware for the Interior AI Service."""

import time
import json
from typing import Callable, Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.logging import StructuredLogger

logger = StructuredLogger("request_logging")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Request and response logging middleware."""
    
    def __init__(self, app, log_requests: bool = True, log_responses: bool = True):
        super().__init__(app)
        self.log_requests = log_requests
        self.log_responses = log_responses
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details."""
        start_time = time.time()
        
        # Log request details
        if self.log_requests:
            await self._log_request(request)
        
        # Process the request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response details
        if self.log_responses:
            await self._log_response(request, response, duration)
        
        return response
    
    async def _log_request(self, request: Request) -> None:
        """Log incoming request details."""
        try:
            # Extract request information
            request_info = {
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "headers": dict(request.headers),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            }
            
            # Try to get request body for POST/PUT requests
            if request.method in ["POST", "PUT", "PATCH"]:
                try:
                    body = await request.body()
                    if body:
                        # Try to parse as JSON
                        try:
                            request_info["body"] = json.loads(body.decode())
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            # If not JSON, just log the size
                            request_info["body_size"] = len(body)
                except Exception:
                    # Ignore body parsing errors
                    pass
            
            logger.info(
                f"📥 Incoming request: {request.method} {request.url.path}",
                **request_info
            )
            
        except Exception as e:
            logger.error(f"❌ Error logging request: {str(e)}")
    
    async def _log_response(self, request: Request, response: Response, duration: float) -> None:
        """Log response details."""
        try:
            # Extract response information
            response_info = {
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_seconds": duration,
                "headers": dict(response.headers),
            }
            
            # Add response body for error responses
            if response.status_code >= 400:
                try:
                    # Try to get response body
                    if hasattr(response, 'body'):
                        body = response.body
                        if isinstance(body, bytes):
                            try:
                                response_info["body"] = json.loads(body.decode())
                            except (json.JSONDecodeError, UnicodeDecodeError):
                                response_info["body_size"] = len(body)
                except Exception:
                    # Ignore body parsing errors
                    pass
            
            # Log based on status code
            if response.status_code >= 500:
                logger.error(
                    f"❌ Server error response: {response.status_code}",
                    **response_info
                )
            elif response.status_code >= 400:
                logger.warning(
                    f"⚠️ Client error response: {response.status_code}",
                    **response_info
                )
            else:
                logger.info(
                    f"📤 Response: {response.status_code} ({duration:.3f}s)",
                    **response_info
                )
            
        except Exception as e:
            logger.error(f"❌ Error logging response: {str(e)}")


def create_logging_middleware(log_requests: bool = True, log_responses: bool = True) -> LoggingMiddleware:
    """Create logging middleware instance."""
    return lambda app: LoggingMiddleware(app, log_requests, log_responses)
