"""Tests for error handling utilities."""

import pytest
from unittest.mock import patch, MagicMock

from app.utils.errors import (
    InteriorAIServiceError,
    DataValidationError,
    ConfigurationError,
    EmailServiceError,
    GenAIServiceError,
    PubSubServiceError,
    AuthenticationError,
    handle_service_error,
    format_error_response,
    log_and_format_error,
    ErrorMonitor,
    create_service_error
)


class TestCustomExceptions:
    """Test custom exception classes."""

    def test_interior_ai_service_error_basic(self):
        """Test basic InteriorAIServiceError functionality."""
        error = InteriorAIServiceError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_data_validation_error(self):
        """Test DataValidationError functionality."""
        error = DataValidationError("Invalid data")
        assert str(error) == "Invalid data"
        assert isinstance(error, InteriorAIServiceError)

    def test_configuration_error(self):
        """Test ConfigurationError functionality."""
        error = ConfigurationError("Missing config")
        assert str(error) == "Missing config"
        assert isinstance(error, InteriorAIServiceError)

    def test_email_service_error(self):
        """Test EmailServiceError functionality."""
        error = EmailServiceError("SMTP connection failed")
        assert str(error) == "SMTP connection failed"
        assert isinstance(error, InteriorAIServiceError)

    def test_genai_service_error(self):
        """Test GenAIServiceError functionality."""
        error = GenAIServiceError("API quota exceeded")
        assert str(error) == "API quota exceeded"
        assert isinstance(error, InteriorAIServiceError)

    def test_pubsub_service_error(self):
        """Test PubSubServiceError functionality."""
        error = PubSubServiceError("Topic not found")
        assert str(error) == "Topic not found"
        assert isinstance(error, InteriorAIServiceError)

    def test_authentication_error(self):
        """Test AuthenticationError functionality."""
        error = AuthenticationError("Invalid credentials")
        assert str(error) == "Invalid credentials"
        assert isinstance(error, InteriorAIServiceError)


class TestErrorHandling:
    """Test error handling functions."""

    def test_handle_service_error_basic(self):
        """Test basic service error handling."""
        error = ValueError("Test error")
        result = handle_service_error(error, "test_service")
        
        assert isinstance(result, InteriorAIServiceError)
        assert "Test error" in str(result)

    def test_handle_service_error_with_context(self):
        """Test service error handling with context."""
        error = ConnectionError("Connection failed")
        result = handle_service_error(error, "email_service", {"operation": "send_email"})
        
        assert isinstance(result, InteriorAIServiceError)
        assert "Connection failed" in str(result)

    def test_format_error_response_basic(self):
        """Test basic error response formatting."""
        error = ValueError("Test error")
        response = format_error_response(error)
        
        assert isinstance(response, dict)
        assert "error" in response
        assert "message" in response["error"]
        assert "Test error" in response["error"]["message"]

    def test_format_error_response_with_details(self):
        """Test error response formatting with details."""
        error = ValueError("Test error")
        response = format_error_response(error, include_details=True)
        
        assert isinstance(response, dict)
        assert "error" in response
        assert "timestamp" in response["error"]

    def test_log_and_format_error_basic(self):
        """Test error logging and formatting."""
        error = ValueError("Test error")
        
        with patch('app.utils.errors.logger') as mock_logger:
            response = log_and_format_error(error)
            
            assert isinstance(response, dict)
            assert "error" in response
            mock_logger.error.assert_called()

    def test_log_and_format_error_with_context(self):
        """Test error logging and formatting with context."""
        error = ValueError("Test error")
        context = {"user_id": "123", "operation": "test"}
        
        with patch('app.utils.errors.logger') as mock_logger:
            response = log_and_format_error(error, context)
            
            assert isinstance(response, dict)
            mock_logger.error.assert_called()

    def test_create_service_error(self):
        """Test service error creation."""
        error = create_service_error("Test message", "validation")
        
        assert isinstance(error, InteriorAIServiceError)
        assert "Test message" in str(error)

    def test_create_service_error_with_kwargs(self):
        """Test service error creation with additional data."""
        error = create_service_error("Test message", "email", smtp_code=550)
        
        assert isinstance(error, InteriorAIServiceError)
        assert "Test message" in str(error)


class TestErrorMonitor:
    """Test ErrorMonitor class."""

    def test_error_monitor_initialization(self):
        """Test ErrorMonitor initialization."""
        monitor = ErrorMonitor()
        assert monitor is not None

    def test_error_monitor_record_error(self):
        """Test error recording."""
        monitor = ErrorMonitor()
        error = ValueError("Test error")
        
        monitor.record_error(error, "test_service")
        
        # Should not raise an exception
        assert True

    def test_error_monitor_get_error_stats(self):
        """Test error statistics retrieval."""
        monitor = ErrorMonitor()
        
        # Record some errors
        monitor.record_error(ValueError("Error 1"), "service1")
        monitor.record_error(ConnectionError("Error 2"), "service2")
        
        stats = monitor.get_error_stats()
        assert isinstance(stats, dict)

    def test_error_monitor_clear_errors(self):
        """Test error clearing."""
        monitor = ErrorMonitor()
        
        # Record an error
        monitor.record_error(ValueError("Test error"), "test_service")
        
        # Clear errors
        monitor.clear_errors()
        
        # Should not raise an exception
        assert True


class TestErrorIntegration:
    """Test error handling integration scenarios."""

    def test_full_error_handling_workflow(self):
        """Test complete error handling workflow."""
        # Simulate a service function that can fail
        def service_function(data):
            if not data.get("email"):
                raise DataValidationError("Email is required")
            if data.get("email") == "invalid":
                raise ValueError("Invalid email format")
            return {"success": True}
        
        # Test successful case
        result = service_function({"email": "test@example.com"})
        assert result["success"] is True
        
        # Test validation error
        try:
            service_function({})
        except DataValidationError as e:
            handled = handle_service_error(e, "validation_service")
            response = format_error_response(handled)
            
            assert response["error"]["message"] == "Email is required"
            assert isinstance(handled, InteriorAIServiceError)

    def test_nested_error_handling(self):
        """Test nested error handling scenarios."""
        def inner_function():
            raise ConnectionError("Database connection failed")
        
        def outer_function():
            try:
                inner_function()
            except ConnectionError as e:
                raise EmailServiceError("Failed to send email") from e
        
        try:
            outer_function()
        except EmailServiceError as e:
            handled = handle_service_error(e, "email_service")
            
            assert isinstance(handled, InteriorAIServiceError)
            assert "Failed to send email" in str(handled)

    def test_error_monitor_integration(self):
        """Test error monitor integration."""
        monitor = ErrorMonitor()
        
        # Simulate multiple errors
        errors = [
            ValueError("Validation error"),
            ConnectionError("Connection error"),
            TimeoutError("Timeout error")
        ]
        
        for error in errors:
            monitor.record_error(error, "test_service")
        
        stats = monitor.get_error_stats()
        assert isinstance(stats, dict)

    def test_error_response_consistency(self):
        """Test error response format consistency."""
        errors = [
            ValueError("Value error"),
            ConnectionError("Connection error"),
            DataValidationError("Validation error"),
            EmailServiceError("Email error")
        ]
        
        responses = []
        for error in errors:
            response = format_error_response(error)
            responses.append(response)
        
        # All responses should have consistent structure
        for response in responses:
            assert isinstance(response, dict)
            assert "error" in response
            assert "message" in response["error"]
            assert "type" in response["error"]
            assert "timestamp" in response["error"]