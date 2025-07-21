"""Unit tests for health check endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import create_app


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_health_check_basic(self, client: TestClient):
        """Test basic health check endpoint."""
        response = client.get("/health/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "service" in data
        assert data["service"] == "interior-ai-service"
        assert data["status"] == "healthy"

    def test_health_readiness_check(self, client: TestClient):
        """Test readiness check endpoint."""
        with patch("app.routers.health.run_authentication_tests") as mock_auth:
            mock_auth.return_value = {
                "overall_status": "healthy",
                "google_cloud_auth": "healthy",
                "vertex_ai_access": "healthy",
                "pubsub_access": "healthy",
                "service_account_permissions": "healthy",
            }
            
            response = client.get("/health/readiness")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "status" in data
            assert "service" in data
            assert "checks" in data
            assert data["service"] == "interior-ai-service"
            assert data["status"] == "healthy"
            assert "google_cloud_auth" in data["checks"]

    def test_health_readiness_check_unhealthy(self, client: TestClient):
        """Test readiness check when authentication fails."""
        with patch("app.routers.health.run_authentication_tests") as mock_auth:
            mock_auth.return_value = {
                "overall_status": "unhealthy",
                "google_cloud_auth": "unhealthy",
                "vertex_ai_access": "unhealthy",
                "pubsub_access": "unhealthy",
                "service_account_permissions": "unhealthy",
            }
            
            response = client.get("/health/readiness")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "unhealthy"
            assert "unhealthy_services" in data

    def test_health_liveness_check(self, client: TestClient):
        """Test liveness check endpoint."""
        response = client.get("/health/liveness")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "service" in data
        assert data["service"] == "interior-ai-service"
        assert data["status"] == "healthy"

    def test_health_startup_check(self, client: TestClient):
        """Test startup check endpoint."""
        response = client.get("/health/startup")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "service" in data
        assert data["service"] == "interior-ai-service"
        assert data["status"] == "healthy"

    def test_health_info_check(self, client: TestClient):
        """Test info check endpoint."""
        response = client.get("/health/info")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "service" in data
        assert "version" in data
        assert "environment" in data
        assert data["service"] == "interior-ai-service"

    def test_health_auth_help(self, client: TestClient):
        """Test authentication help endpoint."""
        response = client.get("/health/auth-help")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "help" in data
        assert "endpoint" in data
        assert "description" in data
        assert data["endpoint"] == "/health/auth-help"
        assert "Google Cloud Authentication Setup Help" in data["help"]


class TestHealthEndpointErrors:
    """Test health endpoint error handling."""

    def test_health_readiness_auth_exception(self, client: TestClient):
        """Test readiness check when authentication test raises exception."""
        with patch("app.routers.health.run_authentication_tests") as mock_auth:
            mock_auth.side_effect = Exception("Authentication test failed")
            
            response = client.get("/health/readiness")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "checks" in data
            assert "google_cloud_auth" in data["checks"]
            assert "error:" in data["checks"]["google_cloud_auth"]

    def test_health_readiness_partial_status(self, client: TestClient):
        """Test readiness check with partial authentication status."""
        with patch("app.routers.health.run_authentication_tests") as mock_auth:
            mock_auth.return_value = {
                "overall_status": "partial",
                "google_cloud_auth": "healthy",
                "vertex_ai_access": "healthy",
                "pubsub_access": "partial",
                "service_account_permissions": "healthy",
            }
            
            response = client.get("/health/readiness")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "checks" in data
            assert data["checks"]["google_cloud_auth"] == "partial" 