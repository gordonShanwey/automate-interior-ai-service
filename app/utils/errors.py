"""Error handling utilities for the Interior AI Service."""

import logging
from typing import Dict, Any, Optional, Union
from datetime import datetime

logger = logging.getLogger(__name__)


class InteriorAIServiceError(Exception):
    """Base exception for Interior AI Service."""
    
    def __init__(self, message: str, error_code: str = "INTERNAL_ERROR", 
                 details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.utcnow()
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format."""
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "timestamp": self.timestamp.isoformat(),
                "details": self.details
            }
        }
    
    def log_error(self) -> None:
        """Log the error with structured information."""
        logger.error(
            f"❌ {self.error_code}: {self.message}",
            extra={
                "error_code": self.error_code,
                "error_details": self.details,
                "timestamp": self.timestamp.isoformat()
            }
        )


class GenAIServiceError(InteriorAIServiceError):
    """Exception for Google Gen AI service errors."""
    
    def __init__(self, message: str, model_used: Optional[str] = None, 
                 prompt_length: Optional[int] = None, response_time: Optional[float] = None):
        details = {}
        if model_used:
            details["model_used"] = model_used
        if prompt_length:
            details["prompt_length"] = prompt_length
        if response_time:
            details["response_time_seconds"] = response_time
        
        super().__init__(message, "GENAI_SERVICE_ERROR", details)


class EmailServiceError(InteriorAIServiceError):
    """Exception for email service errors."""
    
    def __init__(self, message: str, recipient: Optional[str] = None, 
                 template_used: Optional[str] = None, smtp_error: Optional[str] = None):
        details = {}
        if recipient:
            details["recipient"] = recipient
        if template_used:
            details["template_used"] = template_used
        if smtp_error:
            details["smtp_error"] = smtp_error
        
        super().__init__(message, "EMAIL_SERVICE_ERROR", details)


class PubSubServiceError(InteriorAIServiceError):
    """Exception for Pub/Sub service errors."""
    
    def __init__(self, message: str, topic: Optional[str] = None, 
                 subscription: Optional[str] = None, message_id: Optional[str] = None):
        details = {}
        if topic:
            details["topic"] = topic
        if subscription:
            details["subscription"] = subscription
        if message_id:
            details["message_id"] = message_id
        
        super().__init__(message, "PUBSUB_SERVICE_ERROR", details)


class DataValidationError(InteriorAIServiceError):
    """Exception for data validation errors."""
    
    def __init__(self, message: str, field_name: Optional[str] = None, 
                 field_value: Optional[Any] = None, validation_rule: Optional[str] = None):
        details = {}
        if field_name:
            details["field_name"] = field_name
        if field_value is not None:
            details["field_value"] = str(field_value)
        if validation_rule:
            details["validation_rule"] = validation_rule
        
        super().__init__(message, "DATA_VALIDATION_ERROR", details)


class ConfigurationError(InteriorAIServiceError):
    """Exception for configuration errors."""
    
    def __init__(self, message: str, config_key: Optional[str] = None, 
                 config_value: Optional[Any] = None):
        details = {}
        if config_key:
            details["config_key"] = config_key
        if config_value is not None:
            details["config_value"] = str(config_value)
        
        super().__init__(message, "CONFIGURATION_ERROR", details)


class AuthenticationError(InteriorAIServiceError):
    """Exception for authentication errors."""
    
    def __init__(self, message: str, service: Optional[str] = None, 
                 auth_method: Optional[str] = None):
        details = {}
        if service:
            details["service"] = service
        if auth_method:
            details["auth_method"] = auth_method
        
        super().__init__(message, "AUTHENTICATION_ERROR", details)


# Error response formatting utilities
def format_error_response(error: Exception, include_details: bool = False) -> Dict[str, Any]:
    """Format error for API response."""
    if isinstance(error, InteriorAIServiceError):
        response = error.to_dict()
        if not include_details:
            # Remove sensitive details in production
            response["error"].pop("details", None)
        return response
    
    # Handle unexpected errors
    return {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat()
        }
    }


def log_and_format_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Log error and format response."""
    # Log the error
    if isinstance(error, InteriorAIServiceError):
        error.log_error()
    else:
        logger.error(f"❌ Unexpected error: {str(error)}", exc_info=True, extra=context)
    
    # Format response
    return format_error_response(error)


# Error monitoring and alerting helpers
class ErrorMonitor:
    """Error monitoring and alerting utility."""
    
    def __init__(self):
        self.error_counts: Dict[str, int] = {}
        self.error_thresholds: Dict[str, int] = {
            "GENAI_SERVICE_ERROR": 5,
            "EMAIL_SERVICE_ERROR": 3,
            "PUBSUB_SERVICE_ERROR": 3,
            "AUTHENTICATION_ERROR": 2
        }
    
    def record_error(self, error: InteriorAIServiceError) -> None:
        """Record an error and check for alerting."""
        error_type = error.error_code
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # Check if we should alert
        threshold = self.error_thresholds.get(error_type, 10)
        if self.error_counts[error_type] >= threshold:
            self._send_alert(error_type, self.error_counts[error_type])
    
    def _send_alert(self, error_type: str, count: int) -> None:
        """Send alert for high error count."""
        logger.warning(
            f"🚨 ALERT: High error count for {error_type}: {count} errors",
            extra={
                "alert_type": "high_error_count",
                "error_type": error_type,
                "error_count": count,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of recorded errors."""
        return {
            "error_counts": self.error_counts.copy(),
            "total_errors": sum(self.error_counts.values()),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def reset_counts(self) -> None:
        """Reset error counts."""
        self.error_counts.clear()


# Global error monitor instance
error_monitor = ErrorMonitor()


def handle_service_error(error: Exception, service_name: str, 
                        operation: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Centralized error handling for services."""
    context = context or {}
    context.update({
        "service": service_name,
        "operation": operation,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    # Log the error
    logger.error(
        f"❌ {service_name} error during {operation}: {str(error)}",
        exc_info=True,
        extra=context
    )
    
    # Record in monitor if it's our error type
    if isinstance(error, InteriorAIServiceError):
        error_monitor.record_error(error)
    
    # Re-raise the error
    raise error


def create_service_error(message: str, error_type: str, **kwargs) -> InteriorAIServiceError:
    """Factory function to create service-specific errors."""
    error_classes = {
        "genai": GenAIServiceError,
        "email": EmailServiceError,
        "pubsub": PubSubServiceError,
        "validation": DataValidationError,
        "config": ConfigurationError,
        "auth": AuthenticationError
    }
    
    error_class = error_classes.get(error_type, InteriorAIServiceError)
    return error_class(message, **kwargs)
