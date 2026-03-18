"""Unit tests for Firestore-backed message tracking."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from app.services.message_tracker import MessageTracker, PROCESSING_LOCK_TIMEOUT


def _build_tracker(snapshot: MagicMock) -> tuple[MessageTracker, MagicMock, MagicMock]:
    tracker = object.__new__(MessageTracker)
    tracker._db = MagicMock()

    transaction = MagicMock()
    tracker._db.transaction.return_value = transaction

    ref = MagicMock()
    ref.get.return_value = snapshot
    tracker._db.collection.return_value.document.return_value = ref

    return tracker, ref, transaction


def test_check_and_increment_creates_first_attempt() -> None:
    snapshot = MagicMock()
    snapshot.exists = False

    tracker, _, transaction = _build_tracker(snapshot)

    with patch("app.services.message_tracker.firestore.transactional", lambda fn: fn):
        attempt = tracker.check_and_increment("msg-1")

    assert attempt == 1
    transaction.set.assert_called_once()
    transaction.update.assert_not_called()


def test_check_and_increment_skips_processed_message() -> None:
    snapshot = MagicMock()
    snapshot.exists = True
    snapshot.to_dict.return_value = {"status": "processed", "attempts": 1}

    tracker, _, transaction = _build_tracker(snapshot)

    with patch("app.services.message_tracker.firestore.transactional", lambda fn: fn):
        attempt = tracker.check_and_increment("msg-1")

    assert attempt == -1
    transaction.set.assert_not_called()
    transaction.update.assert_not_called()


def test_check_and_increment_skips_recent_in_progress_message() -> None:
    snapshot = MagicMock()
    snapshot.exists = True
    snapshot.to_dict.return_value = {
        "status": "processing",
        "attempts": 1,
        "updated_at": datetime.now(timezone.utc),
    }

    tracker, _, transaction = _build_tracker(snapshot)

    with patch("app.services.message_tracker.firestore.transactional", lambda fn: fn):
        attempt = tracker.check_and_increment("msg-1")

    assert attempt == 0
    transaction.set.assert_not_called()
    transaction.update.assert_not_called()


def test_check_and_increment_retries_stale_in_progress_message() -> None:
    snapshot = MagicMock()
    snapshot.exists = True
    snapshot.to_dict.return_value = {
        "status": "processing",
        "attempts": 2,
        "updated_at": datetime.now(timezone.utc) - PROCESSING_LOCK_TIMEOUT - timedelta(seconds=1),
    }

    tracker, _, transaction = _build_tracker(snapshot)

    with patch("app.services.message_tracker.firestore.transactional", lambda fn: fn):
        attempt = tracker.check_and_increment("msg-1")

    assert attempt == 3
    transaction.update.assert_called_once()
    transaction.set.assert_not_called()
