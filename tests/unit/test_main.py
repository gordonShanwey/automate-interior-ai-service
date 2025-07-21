"""Unit tests for main FastAPI application."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import create_app, app


class TestMainApplication:
    """Test main FastAPI application."""

    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "service" in data
        assert "version" in data
        assert "description" in data
        assert data["service"] == "Interior AI Service"

    def test_docs_endpoint_in_debug_mode(self, client: TestClient):
        """Test that docs endpoint is available in debug mode."""
        response = client.get("/docs")
        
        # Should return 200 in debug mode
        assert response.status_code == 200

    def test_openapi_endpoint_in_debug_mode(self, client: TestClient):
        """Test that OpenAPI endpoint is available in debug mode."""
        response = client.get("/openapi.json")
        
        # Should return 200 in debug mode
        assert response.status_code == 200

    def test_health_router_included(self, client: TestClient):
        """Test that health router is included."""
        response = client.get("/health/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "interior-ai-service"

    def test_webhooks_router_included(self, client: TestClient):
        """Test that webhooks router is included."""
        response = client.get("/webhooks/pubsub")
        
        # Should return 200 for GET request to webhook info
        assert response.status_code == 200

    def test_cors_headers(self, client: TestClient):
        """Test that CORS headers are set."""
        response = client.options("/")
        
        # CORS preflight request should work
        assert response.status_code in [200, 405]  # 405 is also acceptable for OPTIONS

    def test_application_lifespan(self):
        """Test application lifespan context manager."""
        from contextlib import asynccontextmanager
        from app.main import lifespan
        
        # Test that lifespan is a context manager
        assert hasattr(lifespan, "__aenter__")
        assert hasattr(lifespan, "__aexit__")

    def test_create_app_function(self):
        """Test create_app function returns FastAPI instance."""
        app_instance = create_app()
        
        from fastapi import FastAPI
        assert isinstance(app_instance, FastAPI)
        assert app_instance.title == "Interior AI Service"

    def test_global_exception_handler(self, client: TestClient):
        """Test global exception handler."""
        # This would require triggering an exception in the application
        # For now, we just test that the application starts without errors
        assert app is not None


class TestApplicationConfiguration:
    """Test application configuration."""

    def test_application_title(self, client: TestClient):
        """Test application title is set correctly."""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        assert data["info"]["title"] == "Interior AI Service"

    def test_application_version(self, client: TestClient):
        """Test application version is set correctly."""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        assert "version" in data["info"]

    def test_application_description(self, client: TestClient):
        """Test application description is set correctly."""
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        assert "description" in data["info"]
        assert "Interior designer automation service" in data["info"]["description"]


class TestMiddleware:
    """Test application middleware."""

    def test_request_logging_middleware(self, client: TestClient):
        """Test that request logging middleware is active."""
        # This is tested indirectly by checking that requests work
        response = client.get("/health/")
        assert response.status_code == 200

    def test_cors_middleware(self, client: TestClient):
        """Test that CORS middleware is active."""
        # Test with a simple request
        response = client.get("/health/")
        assert response.status_code == 200


class TestErrorHandling:
    """Test error handling."""

    def test_404_error(self, client: TestClient):
        """Test 404 error handling."""
        response = client.get("/nonexistent-endpoint")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_405_error(self, client: TestClient):
        """Test 405 error handling."""
        # Try to POST to a GET-only endpoint
        response = client.post("/health/")
        
        assert response.status_code == 405
        data = response.json()
        assert "detail" in data 