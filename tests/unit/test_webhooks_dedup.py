"""Focused webhook tests for Pub/Sub deduplication behavior."""

import base64
import json
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


def _pubsub_message(message_id: str = "test-message-id") -> dict[str, object]:
    payload = {"name": "John Doe", "email": "john@example.com"}
    return {
        "message": {
            "data": base64.b64encode(json.dumps(payload).encode()).decode(),
            "messageId": message_id,
            "publishTime": "2026-03-18T16:48:13Z",
        },
        "subscription": "projects/test-project/subscriptions/test-subscription",
    }


def test_pubsub_duplicate_in_progress_message_is_acknowledged_without_processing(
    client: TestClient,
) -> None:
    tracker = MagicMock()
    tracker.check_and_increment.return_value = 0

    with patch("app.routers.webhooks.get_message_tracker", return_value=tracker), patch(
        "app.routers.webhooks.process_client_profile_generation"
    ) as background_task:
        response = client.post("/webhooks/pubsub", json=_pubsub_message())

    assert response.status_code == 204
    background_task.assert_not_called()


def test_pubsub_tracker_failure_returns_retryable_error(client: TestClient) -> None:
    with patch(
        "app.routers.webhooks.get_message_tracker",
        side_effect=RuntimeError("firestore unavailable"),
    ), patch("app.routers.webhooks.process_client_profile_generation") as background_task:
        response = client.post("/webhooks/pubsub", json=_pubsub_message())

    assert response.status_code == 500
    background_task.assert_not_called()
