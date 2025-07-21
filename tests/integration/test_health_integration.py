"""Integration tests for health endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock


class TestHealthIntegration:
    """Integration tests for health check endpoints."""

    @pytest.mark.integration
    def test_health_endpoints_workflow(self, client: TestClient):
        """Test complete health check workflow."""
        # Test basic health check
        response = client.get("/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "interior-ai-service"

        # Test liveness check
        response = client.get("/health/liveness")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

        # Test startup check
        response = client.get("/health/startup")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

        # Test info check
        response = client.get("/health/info")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "environment" in data

    @pytest.mark.integration
    def test_readiness_check_with_mocked_auth(self, client: TestClient):
        """Test readiness check with mocked authentication."""
        with patch("app.routers.health.run_authentication_tests") as mock_auth:
            mock_auth.return_value = {
                "overall_status": "healthy",
                "google_cloud_auth": "healthy",
                "vertex_ai_access": "healthy",
                "pubsub_access": "healthy",
                "service_account_permissions": "healthy",
                "auth_details": {
                    "google_cloud_auth": {"status": "healthy", "project_id": "test-project"},
                    "vertex_ai_access": {"status": "healthy", "location": "us-central1"},
                    "pubsub_access": {"status": "healthy", "topic": "test-topic"},
                    "service_account_permissions": {"status": "healthy", "roles": ["aiplatform.user"]},
                }
            }
            
            response = client.get("/health/readiness")
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "healthy"
            assert "checks" in data
            assert "auth_details" in data
            assert data["checks"]["google_cloud_auth"] == "healthy"

    @pytest.mark.integration
    def test_readiness_check_with_partial_failures(self, client: TestClient):
        """Test readiness check with partial authentication failures."""
        with patch("app.routers.health.run_authentication_tests") as mock_auth:
            mock_auth.return_value = {
                "overall_status": "partial",
                "google_cloud_auth": "healthy",
                "vertex_ai_access": "healthy",
                "pubsub_access": "partial",
                "service_account_permissions": "healthy",
                "auth_details": {
                    "google_cloud_auth": {"status": "healthy", "project_id": "test-project"},
                    "vertex_ai_access": {"status": "healthy", "location": "us-central1"},
                    "pubsub_access": {"status": "partial", "error": "Topic not found"},
                    "service_account_permissions": {"status": "healthy", "roles": ["aiplatform.user"]},
                }
            }
            
            response = client.get("/health/readiness")
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "unhealthy"
            assert "unhealthy_services" in data
            assert "google_cloud_auth" in data["unhealthy_services"]

    @pytest.mark.integration
    def test_auth_help_endpoint(self, client: TestClient):
        """Test authentication help endpoint."""
        response = client.get("/health/auth-help")
        assert response.status_code == 200
        data = response.json()
        
        assert "help" in data
        assert "endpoint" in data
        assert "description" in data
        assert data["endpoint"] == "/health/auth-help"
        
        # Check that help text contains expected sections
        help_text = data["help"]
        assert "Google Cloud Authentication Setup Help" in help_text
        assert "For Local Development:" in help_text
        assert "For Production:" in help_text
        assert "Required Environment Variables:" in help_text
        assert "Test Authentication:" in help_text

    @pytest.mark.integration
    def test_health_endpoints_response_structure(self, client: TestClient):
        """Test that all health endpoints return consistent response structure."""
        endpoints = [
            "/health/",
            "/health/liveness",
            "/health/startup",
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200
            data = response.json()
            
            # All health endpoints should have these fields
            assert "status" in data
            assert "service" in data
            assert data["service"] == "interior-ai-service"
            assert data["status"] in ["healthy", "unhealthy"]

    @pytest.mark.integration
    def test_health_endpoints_headers(self, client: TestClient):
        """Test that health endpoints return proper headers."""
        response = client.get("/health/")
        assert response.status_code == 200
        
        # Check for expected headers
        headers = response.headers
        assert "content-type" in headers
        assert "application/json" in headers["content-type"]

    @pytest.mark.integration
    def test_health_endpoints_error_handling(self, client: TestClient):
        """Test error handling in health endpoints."""
        # Test with invalid HTTP method
        response = client.post("/health/")
        assert response.status_code == 405  # Method Not Allowed
        
        response = client.put("/health/readiness")
        assert response.status_code == 405  # Method Not Allowed

    @pytest.mark.integration
    def test_readiness_check_with_auth_exception(self, client: TestClient):
        """Test readiness check when authentication test raises exception."""
        with patch("app.routers.health.run_authentication_tests") as mock_auth:
            mock_auth.side_effect = Exception("Authentication service unavailable")
            
            response = client.get("/health/readiness")
            assert response.status_code == 200
            data = response.json()
            
            assert "checks" in data
            assert "google_cloud_auth" in data["checks"]
            assert "error:" in data["checks"]["google_cloud_auth"]

    @pytest.mark.integration
    def test_health_endpoints_performance(self, client: TestClient):
        """Test that health endpoints respond quickly."""
        import time
        
        # Test basic health check performance
        start_time = time.time()
        response = client.get("/health/")
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Should respond within 1 second

        # Test readiness check performance (with mocked auth)
        with patch("app.routers.health.run_authentication_tests") as mock_auth:
            mock_auth.return_value = {
                "overall_status": "healthy",
                "google_cloud_auth": "healthy",
                "vertex_ai_access": "healthy",
                "pubsub_access": "healthy",
                "service_account_permissions": "healthy",
            }
            
            start_time = time.time()
            response = client.get("/health/readiness")
            end_time = time.time()
            
            assert response.status_code == 200
            assert (end_time - start_time) < 2.0  # Should respond within 2 seconds 