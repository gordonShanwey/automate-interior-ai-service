"""Logging utilities for the Interior AI Service."""

import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional, Union
from google.cloud import logging as google_logging

from app.config import get_settings


def setup_logging() -> None:
    """Setup structured logging with Google Cloud Logging integration."""
    settings = get_settings()
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Setup Google Cloud Logging if in production
    if settings.environment == "production":
        setup_google_cloud_logging()
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    
    logger = logging.getLogger(__name__)
    logger.info(f"🚀 Logging initialized for {settings.app_name} v{settings.app_version}")


def setup_google_cloud_logging() -> None:
    """Setup Google Cloud Logging client."""
    try:
        client = google_logging.Client()
        client.setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("☁️ Google Cloud Logging configured")
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning(f"⚠️ Failed to setup Google Cloud Logging: {e}")


class StructuredLogger:
    """Structured logging utility for consistent log formatting."""
    
    def __init__(self, logger_name: str):
        self.logger = logging.getLogger(logger_name)
    
    def _format_extra(self, **kwargs) -> Dict[str, Any]:
        """Format extra fields for structured logging."""
        extra = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": "interior-ai-service"
        }
        extra.update(kwargs)
        return extra
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message with structured data."""
        self.logger.info(message, extra=self._format_extra(**kwargs))
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message with structured data."""
        self.logger.warning(message, extra=self._format_extra(**kwargs))
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message with structured data."""
        self.logger.error(message, extra=self._format_extra(**kwargs))
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message with structured data."""
        self.logger.debug(message, extra=self._format_extra(**kwargs))
    
    def critical(self, message: str, **kwargs) -> None:
        """Log critical message with structured data."""
        self.logger.critical(message, extra=self._format_extra(**kwargs))


def log_data_structure(data: Dict[str, Any], context: str = "data_analysis") -> None:
    """Log data structure for analysis purposes."""
    logger = StructuredLogger("data_analysis")
    
    # Analyze data structure
    structure_info = {
        "field_count": len(data),
        "field_names": list(data.keys()),
        "field_types": {},
        "nested_structures": [],
        "array_fields": [],
        "null_fields": []
    }
    
    for key, value in data.items():
        field_type = type(value).__name__
        if field_type not in structure_info["field_types"]:
            structure_info["field_types"][field_type] = []
        structure_info["field_types"][field_type].append(key)
        
        # Track special structures
        if isinstance(value, dict):
            structure_info["nested_structures"].append(key)
        elif isinstance(value, list):
            structure_info["array_fields"].append(key)
        elif value is None:
            structure_info["null_fields"].append(key)
    
    logger.info(
        f"📊 Data structure analysis for {context}",
        context=context,
        structure_info=structure_info,
        sample_data={k: str(v)[:100] + "..." if len(str(v)) > 100 else str(v) 
                    for k, v in list(data.items())[:5]}  # First 5 fields
    )


def log_performance_metric(operation: str, duration_seconds: float, 
                          success: bool = True, **kwargs) -> None:
    """Log performance metrics."""
    logger = StructuredLogger("performance")
    
    logger.info(
        f"⏱️ Performance metric: {operation}",
        operation=operation,
        duration_seconds=duration_seconds,
        success=success,
        **kwargs
    )


def log_service_operation(service: str, operation: str, 
                         status: str = "started", **kwargs) -> None:
    """Log service operation lifecycle."""
    logger = StructuredLogger("service_operations")
    
    logger.info(
        f"🔧 {service} {operation}: {status}",
        service=service,
        operation=operation,
        status=status,
        **kwargs
    )


def log_ai_interaction(model: str, prompt_length: int, response_length: int,
                      duration_seconds: float, success: bool = True, **kwargs) -> None:
    """Log AI interaction metrics."""
    logger = StructuredLogger("ai_interactions")
    
    logger.info(
        f"🤖 AI interaction with {model}",
        model=model,
        prompt_length=prompt_length,
        response_length=response_length,
        duration_seconds=duration_seconds,
        success=success,
        **kwargs
    )


def log_email_operation(recipient: str, template: str, status: str, **kwargs) -> None:
    """Log email operation metrics."""
    logger = StructuredLogger("email_operations")
    
    logger.info(
        f"📧 Email {status} to {recipient}",
        recipient=recipient,
        template=template,
        status=status,
        **kwargs
    )


def log_pubsub_message(topic: str, message_id: str, status: str, **kwargs) -> None:
    """Log Pub/Sub message processing."""
    logger = StructuredLogger("pubsub_operations")
    
    logger.info(
        f"📨 Pub/Sub message {status} from {topic}",
        topic=topic,
        message_id=message_id,
        status=status,
        **kwargs
    )


# Performance monitoring helpers
class PerformanceMonitor:
    """Performance monitoring utility."""
    
    def __init__(self):
        self.metrics: Dict[str, list] = {}
    
    def record_metric(self, operation: str, duration_seconds: float, 
                     success: bool = True, **kwargs) -> None:
        """Record a performance metric."""
        if operation not in self.metrics:
            self.metrics[operation] = []
        
        metric = {
            "timestamp": datetime.utcnow().isoformat(),
            "duration_seconds": duration_seconds,
            "success": success,
            **kwargs
        }
        
        self.metrics[operation].append(metric)
        
        # Keep only last 100 metrics per operation
        if len(self.metrics[operation]) > 100:
            self.metrics[operation] = self.metrics[operation][-100:]
        
        # Log the metric
        log_performance_metric(operation, duration_seconds, success, **kwargs)
    
    def get_operation_stats(self, operation: str) -> Dict[str, Any]:
        """Get statistics for an operation."""
        if operation not in self.metrics:
            return {}
        
        metrics = self.metrics[operation]
        if not metrics:
            return {}
        
        durations = [m["duration_seconds"] for m in metrics]
        success_count = sum(1 for m in metrics if m["success"])
        
        return {
            "operation": operation,
            "total_calls": len(metrics),
            "success_rate": success_count / len(metrics),
            "avg_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "last_updated": datetime.utcnow().isoformat()
        }
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all operations."""
        return {
            operation: self.get_operation_stats(operation)
            for operation in self.metrics.keys()
        }


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


# Context manager for timing operations
import time
from contextlib import contextmanager


@contextmanager
def timed_operation(operation: str, **kwargs):
    """Context manager for timing operations."""
    start_time = time.time()
    success = False
    
    try:
        yield
        success = True
    except Exception as e:
        logger = StructuredLogger("performance")
        logger.error(f"❌ Operation {operation} failed: {str(e)}")
        raise
    finally:
        duration = time.time() - start_time
        performance_monitor.record_metric(operation, duration, success, **kwargs)


# Data quality logging
def log_data_quality_assessment(data: Dict[str, Any], quality_score: float,
                               missing_fields: list, unmapped_fields: list) -> None:
    """Log data quality assessment results."""
    logger = StructuredLogger("data_quality")
    
    logger.info(
        f"📋 Data quality assessment completed",
        quality_score=quality_score,
        total_fields=len(data),
        missing_fields=missing_fields,
        unmapped_fields=unmapped_fields,
        field_count=len(data)
    )


# Service health logging
def log_service_health(service: str, status: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Log service health status."""
    logger = StructuredLogger("service_health")
    
    logger.info(
        f"🏥 {service} health check: {status}",
        service=service,
        status=status,
        details=details or {}
    )
