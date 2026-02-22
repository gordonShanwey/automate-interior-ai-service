"""Firestore-based Pub/Sub message deduplication and retry tracking."""

import logging
from datetime import datetime, timezone
from typing import Optional

from google.cloud import firestore

from app.config import get_settings

logger = logging.getLogger(__name__)

COLLECTION = "pubsub_messages"
MAX_ATTEMPTS = 5


class MessageTracker:
    """
    Tracks Pub/Sub message processing state in Firestore.

    Solves two problems:
    - Cold start retries: Cloud Run min=0 causes Pub/Sub to redeliver before
      receiving the 204, resulting in duplicate AI calls and duplicate emails.
    - Cross-instance deduplication: in-memory counters reset on each instance.

    Firestore document structure (collection: pubsub_messages):
        {
            "attempts": 2,
            "status": "processing" | "processed",
            "created_at": <timestamp>,
            "updated_at": <timestamp>,
            "processed_at": <timestamp>   # only when status == "processed"
        }
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._db = firestore.Client(project=settings.google_cloud_project)

    def check_and_increment(self, message_id: str) -> int:
        """
        Atomically check and increment the attempt counter for a message.

        Returns:
            -1  if the message was already successfully processed (skip it)
             N  the new attempt count (1 = first attempt, 2 = first retry…)
        """
        ref = self._db.collection(COLLECTION).document(message_id)

        @firestore.transactional
        def _update(transaction: firestore.Transaction) -> int:
            snapshot = ref.get(transaction=transaction)
            if snapshot.exists:
                data = snapshot.to_dict() or {}
                if data.get("status") == "processed":
                    return -1
                attempts = data.get("attempts", 0) + 1
                transaction.update(ref, {
                    "attempts": attempts,
                    "status": "processing",
                    "updated_at": datetime.now(timezone.utc),
                })
            else:
                attempts = 1
                transaction.set(ref, {
                    "attempts": attempts,
                    "status": "processing",
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                })
            return attempts

        return _update(self._db.transaction())

    def mark_processed(self, message_id: str) -> None:
        """Mark a message as successfully processed."""
        self._db.collection(COLLECTION).document(message_id).update({
            "status": "processed",
            "processed_at": datetime.now(timezone.utc),
        })


_tracker_instance: Optional[MessageTracker] = None


def get_message_tracker() -> MessageTracker:
    """Get the global message tracker instance."""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = MessageTracker()
    return _tracker_instance
