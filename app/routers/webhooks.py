"""Pub/Sub webhook handlers for the Interior AI Service."""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Request, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/pubsub")
async def handle_pubsub_push_notification(request: Request) -> Dict[str, str]:
    """Handle incoming Pub/Sub push notifications with client form data."""
    # TODO: Implement Pub/Sub message processing
    # This will be implemented in Phase 2: Data Models & Core Services
    
    logger.info("📨 Received Pub/Sub push notification")
    
    return {
        "status": "received",
        "message": "Pub/Sub notification received (processing not yet implemented)",
        "endpoint": "/webhooks/pubsub"
    }


@router.get("/pubsub")
async def pubsub_webhook_info() -> Dict[str, Any]:
    """Get information about the Pub/Sub webhook endpoint."""
    return {
        "endpoint": "/webhooks/pubsub",
        "method": "POST",
        "description": "Handles Pub/Sub push notifications with client form data",
        "status": "placeholder",
        "implementation": "Phase 2"
    }
