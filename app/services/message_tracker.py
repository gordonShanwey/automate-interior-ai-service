"""Firestore-based Pub/Sub message deduplication and retry tracking."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from google.cloud import firestore

from app.config import get_settings

logger = logging.getLogger(__name__)

COLLECTION = "pubsub_messages"
MAX_ATTEMPTS = 5
PROCESSING_LOCK_TIMEOUT = timedelta(minutes=10)


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
             0  if the message is already being processed by another worker
             N  the new attempt count (1 = first attempt, 2 = first retry…)
        """
        ref = self._db.collection(COLLECTION).document(message_id)

        def _normalize_timestamp(value: object) -> Optional[datetime]:
            if not isinstance(value, datetime):
                return None
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)

        def _update(transaction: firestore.Transaction) -> int:
            now = datetime.now(timezone.utc)
            snapshot = ref.get(transaction=transaction)
            if snapshot.exists:
                data = snapshot.to_dict() or {}
                status = data.get("status")
                attempts = int(data.get("attempts", 0))

                if status == "processed":
                    return -1

                updated_at = _normalize_timestamp(data.get("updated_at"))
                if (
                    status == "processing"
                    and updated_at is not None
                    and now - updated_at < PROCESSING_LOCK_TIMEOUT
                ):
                    return 0

                attempts += 1
                transaction.update(ref, {
                    "attempts": attempts,
                    "status": "processing",
                    "updated_at": now,
                })
            else:
                attempts = 1
                transaction.set(ref, {
                    "attempts": attempts,
                    "status": "processing",
                    "created_at": now,
                    "updated_at": now,
                })
            return attempts

        transaction = self._db.transaction()
        return firestore.transactional(_update)(transaction)

    def mark_processed(self, message_id: str) -> None:
        """Mark a message as successfully processed."""
        self._db.collection(COLLECTION).document(message_id).update({
            "status": "processed",
            "processed_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        })


_tracker_instance: Optional[MessageTracker] = None


def get_message_tracker() -> MessageTracker:
    """Get the global message tracker instance."""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = MessageTracker()
    return _tracker_instance
