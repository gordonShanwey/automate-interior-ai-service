"""Pytest configuration and common fixtures for Interior AI Service tests."""

import asyncio
import logging
from typing import AsyncGenerator, Dict, Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import create_app
from app.config import get_settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def app() -> FastAPI:
    """Create a FastAPI application instance for testing."""
    return create_app()


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
async def async_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for the FastAPI application."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_settings() -> Dict[str, Any]:
    """Mock settings for testing."""
    return {
        "app_name": "Interior AI Service Test",
        "app_version": "0.1.0",
        "environment": "test",
        "debug": True,
        "log_level": "DEBUG",
        "google_cloud_project": "test-project",
        "vertex_ai_location": "us-central1",
        "genai_model": "gemini-2.5-pro",
        "pubsub_topic": "test-topic",
        "pubsub_subscription": "test-subscription",
        "smtp_server": "smtp.test.com",
        "smtp_port": 587,
        "smtp_username": "test@test.com",
        "smtp_password": "test-password",
        "designer_email": "designer@test.com",
    }


@pytest.fixture
def mock_google_cloud_auth():
    """Mock Google Cloud authentication."""
    mock_credentials = MagicMock()
    mock_credentials.project_id = "test-project"
    mock_credentials.token = "test-token"
    
    mock_auth = AsyncMock()
    mock_auth.return_value = (mock_credentials, "test-project")
    
    return mock_auth


@pytest.fixture
def mock_genai_client():
    """Mock Google GenAI client."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.text = "Test response from GenAI"
    mock_client.models.generate_content.return_value = mock_response
    
    return mock_client


@pytest.fixture
def mock_pubsub_client():
    """Mock Google Pub/Sub client."""
    mock_publisher = AsyncMock()
    mock_subscriber = AsyncMock()
    
    # Mock topic and subscription info
    mock_topic = MagicMock()
    mock_topic.name = "projects/test-project/topics/test-topic"
    
    mock_subscription = MagicMock()
    mock_subscription.name = "projects/test-project/subscriptions/test-subscription"
    mock_subscription.topic = "projects/test-project/topics/test-topic"
    mock_subscription.push_config = None
    mock_subscription.ack_deadline_seconds = 10
    mock_subscription.retain_acked_messages = False
    
    mock_publisher.get_topic.return_value = mock_topic
    mock_subscriber.get_subscription.return_value = mock_subscription
    
    return {
        "publisher": mock_publisher,
        "subscriber": mock_subscriber,
    }


@pytest.fixture
def sample_client_data() -> Dict[str, Any]:
    """Sample client data for testing."""
    return {
        "client_name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1234567890",
        "project_type": "Living Room Redesign",
        "budget_range": "$10,000 - $15,000",
        "timeline": "3-6 months",
        "preferred_style": "Modern",
        "room_size": "500 sq ft",
        "additional_requirements": "Eco-friendly materials, pet-friendly furniture",
    }


@pytest.fixture
def sample_pubsub_message() -> Dict[str, Any]:
    """Sample Pub/Sub message for testing."""
    import base64
    import json
    
    message_data = {
        "client_name": "Jane Smith",
        "email": "jane.smith@example.com",
        "project_type": "Kitchen Remodel",
        "budget_range": "$20,000 - $30,000",
        "timeline": "6-12 months",
    }
    
    return {
        "message": {
            "data": base64.b64encode(json.dumps(message_data).encode()).decode(),
            "messageId": "test-message-id",
            "publishTime": "2024-01-01T00:00:00Z",
        },
        "subscription": "projects/test-project/subscriptions/test-subscription",
    }


@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    mock_logger = MagicMock(spec=logging.Logger)
    mock_logger.info = MagicMock()
    mock_logger.error = MagicMock()
    mock_logger.warning = MagicMock()
    mock_logger.debug = MagicMock()
    
    return mock_logger


# Test markers for different test types
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


# Helper functions for testing
def create_test_app() -> FastAPI:
    """Create a test application with test settings."""
    # This could be used to create an app with specific test configurations
    return create_app()


def assert_response_structure(response_data: Dict[str, Any], expected_keys: list) -> None:
    """Assert that response data contains expected keys."""
    for key in expected_keys:
        assert key in response_data, f"Expected key '{key}' not found in response"


def assert_health_check_response(response_data: Dict[str, Any]) -> None:
    """Assert that health check response has correct structure."""
    expected_keys = ["status", "service"]
    assert_response_structure(response_data, expected_keys)
    assert response_data["service"] == "interior-ai-service"
    assert response_data["status"] in ["healthy", "unhealthy"]
