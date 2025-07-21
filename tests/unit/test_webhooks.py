"""Unit tests for webhook endpoints."""

import pytest
import json
import base64
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


class TestWebhookEndpoints:
    """Test webhook endpoints."""

    def test_pubsub_webhook_info(self, client: TestClient):
        """Test GET endpoint for Pub/Sub webhook info."""
        response = client.get("/webhooks/pubsub")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "endpoint" in data
        assert "description" in data
        assert "method" in data
        assert data["endpoint"] == "/webhooks/pubsub"
        assert data["method"] == "POST"

    def test_pubsub_webhook_invalid_method(self, client: TestClient):
        """Test that GET request to POST-only endpoint returns info."""
        response = client.get("/webhooks/pubsub")
        
        # Should return info about the endpoint, not 405
        assert response.status_code == 200
        data = response.json()
        assert "description" in data

    def test_pubsub_webhook_put_method(self, client: TestClient):
        """Test that PUT request returns 405."""
        response = client.put("/webhooks/pubsub")
        
        assert response.status_code == 405  # Method Not Allowed

    def test_pubsub_webhook_delete_method(self, client: TestClient):
        """Test that DELETE request returns 405."""
        response = client.delete("/webhooks/pubsub")
        
        assert response.status_code == 405  # Method Not Allowed


class TestPubSubMessageHandling:
    """Test Pub/Sub message handling."""

    def test_pubsub_push_notification_valid_message(self, client: TestClient):
        """Test handling of valid Pub/Sub push notification."""
        # Create a valid Pub/Sub push message
        message_data = {
            "client_name": "John Doe",
            "email": "john@example.com",
            "project_type": "Living Room Redesign",
            "budget_range": "$10,000 - $15,000",
        }
        
        pubsub_message = {
            "message": {
                "data": base64.b64encode(json.dumps(message_data).encode()).decode(),
                "messageId": "test-message-id-123",
                "publishTime": "2024-01-01T00:00:00Z",
            },
            "subscription": "projects/test-project/subscriptions/test-subscription",
        }
        
        response = client.post(
            "/webhooks/pubsub",
            json=pubsub_message,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "messageId" in data
        assert data["status"] == "received"
        assert data["messageId"] == "test-message-id-123"

    def test_pubsub_push_notification_missing_message(self, client: TestClient):
        """Test handling of Pub/Sub message without 'message' field."""
        invalid_message = {
            "subscription": "projects/test-project/subscriptions/test-subscription",
        }
        
        response = client.post(
            "/webhooks/pubsub",
            json=invalid_message,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 400
        data = response.json()
        
        assert "detail" in data
        assert "Invalid Pub/Sub message format" in data["detail"]

    def test_pubsub_push_notification_missing_data(self, client: TestClient):
        """Test handling of Pub/Sub message without 'data' field."""
        invalid_message = {
            "message": {
                "messageId": "test-message-id-123",
                "publishTime": "2024-01-01T00:00:00Z",
            },
            "subscription": "projects/test-project/subscriptions/test-subscription",
        }
        
        response = client.post(
            "/webhooks/pubsub",
            json=invalid_message,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 400
        data = response.json()
        
        assert "detail" in data
        assert "No data in Pub/Sub message" in data["detail"]

    def test_pubsub_push_notification_invalid_json(self, client: TestClient):
        """Test handling of Pub/Sub message with invalid JSON data."""
        pubsub_message = {
            "message": {
                "data": base64.b64encode(b"invalid json data").decode(),
                "messageId": "test-message-id-123",
                "publishTime": "2024-01-01T00:00:00Z",
            },
            "subscription": "projects/test-project/subscriptions/test-subscription",
        }
        
        response = client.post(
            "/webhooks/pubsub",
            json=pubsub_message,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 400
        data = response.json()
        
        assert "detail" in data
        assert "Invalid JSON format" in data["detail"]

    def test_pubsub_push_notification_invalid_base64(self, client: TestClient):
        """Test handling of Pub/Sub message with invalid base64 data."""
        pubsub_message = {
            "message": {
                "data": "invalid-base64-data",
                "messageId": "test-message-id-123",
                "publishTime": "2024-01-01T00:00:00Z",
            },
            "subscription": "projects/test-project/subscriptions/test-subscription",
        }
        
        response = client.post(
            "/webhooks/pubsub",
            json=pubsub_message,
            headers={"Content-Type": "application/json"}
        )
        
        # Should handle base64 decode error gracefully
        assert response.status_code in [400, 500]

    def test_pubsub_push_notification_empty_data(self, client: TestClient):
        """Test handling of Pub/Sub message with empty data."""
        pubsub_message = {
            "message": {
                "data": base64.b64encode(json.dumps({}).encode()).decode(),
                "messageId": "test-message-id-123",
                "publishTime": "2024-01-01T00:00:00Z",
            },
            "subscription": "projects/test-project/subscriptions/test-subscription",
        }
        
        response = client.post(
            "/webhooks/pubsub",
            json=pubsub_message,
            headers={"Content-Type": "application/json"}
        )
        
        # Should accept empty data
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "received"

    def test_pubsub_push_notification_complex_data(self, client: TestClient):
        """Test handling of Pub/Sub message with complex data structure."""
        message_data = {
            "client_name": "Jane Smith",
            "email": "jane@example.com",
            "phone": "+1234567890",
            "project_type": "Kitchen Remodel",
            "budget_range": "$20,000 - $30,000",
            "timeline": "6-12 months",
            "preferred_style": "Modern",
            "room_size": "400 sq ft",
            "additional_requirements": [
                "Eco-friendly materials",
                "Pet-friendly furniture",
                "Open concept design"
            ],
            "contact_preferences": {
                "phone": True,
                "email": True,
                "text": False
            }
        }
        
        pubsub_message = {
            "message": {
                "data": base64.b64encode(json.dumps(message_data).encode()).decode(),
                "messageId": "test-message-id-complex",
                "publishTime": "2024-01-01T00:00:00Z",
            },
            "subscription": "projects/test-project/subscriptions/test-subscription",
        }
        
        response = client.post(
            "/webhooks/pubsub",
            json=pubsub_message,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "received"
        assert data["messageId"] == "test-message-id-complex"

    def test_pubsub_push_notification_missing_message_id(self, client: TestClient):
        """Test handling of Pub/Sub message without messageId."""
        message_data = {"client_name": "John Doe", "email": "john@example.com"}
        
        pubsub_message = {
            "message": {
                "data": base64.b64encode(json.dumps(message_data).encode()).decode(),
                "publishTime": "2024-01-01T00:00:00Z",
            },
            "subscription": "projects/test-project/subscriptions/test-subscription",
        }
        
        response = client.post(
            "/webhooks/pubsub",
            json=pubsub_message,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "received"
        assert data["messageId"] == "unknown"


class TestWebhookErrorHandling:
    """Test webhook error handling."""

    def test_pubsub_webhook_internal_error(self, client: TestClient):
        """Test handling of internal server error in webhook."""
        # This would require mocking the background task to raise an exception
        # For now, we test the basic structure
        message_data = {"test": "data"}
        
        pubsub_message = {
            "message": {
                "data": base64.b64encode(json.dumps(message_data).encode()).decode(),
                "messageId": "test-message-id-error",
                "publishTime": "2024-01-01T00:00:00Z",
            },
            "subscription": "projects/test-project/subscriptions/test-subscription",
        }
        
        response = client.post(
            "/webhooks/pubsub",
            json=pubsub_message,
            headers={"Content-Type": "application/json"}
        )
        
        # Should still return 200 even if background processing fails
        assert response.status_code == 200

    def test_pubsub_webhook_malformed_request(self, client: TestClient):
        """Test handling of malformed request body."""
        response = client.post(
            "/webhooks/pubsub",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422  # Unprocessable Entity

    def test_pubsub_webhook_missing_content_type(self, client: TestClient):
        """Test handling of request without Content-Type header."""
        message_data = {"test": "data"}
        
        pubsub_message = {
            "message": {
                "data": base64.b64encode(json.dumps(message_data).encode()).decode(),
                "messageId": "test-message-id",
                "publishTime": "2024-01-01T00:00:00Z",
            },
            "subscription": "projects/test-project/subscriptions/test-subscription",
        }
        
        response = client.post(
            "/webhooks/pubsub",
            json=pubsub_message
            # No Content-Type header
        )
        
        # Should still work as FastAPI can infer JSON
        assert response.status_code == 200 