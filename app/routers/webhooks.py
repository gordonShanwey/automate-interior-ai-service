"""Webhook endpoints for the Interior AI Service."""

import json
import base64
from typing import Dict, Any
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, status
from fastapi.responses import JSONResponse, Response

from app.models.client_data import RawClientData
from app.services.message_tracker import MAX_ATTEMPTS, get_message_tracker
from app.services.pubsub_service import process_message_callback
from app.utils.errors import format_error_response
from app.utils.logging import StructuredLogger, log_pubsub_message
from app.config import get_settings

logger = StructuredLogger("webhooks")
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/pubsub", status_code=status.HTTP_204_NO_CONTENT)
async def handle_pubsub_push_notification(
    request: Request,
    background_tasks: BackgroundTasks
) -> Response:
    """
    Handle Pub/Sub push notifications for client form data.

    Returns 204 to acknowledge (stop retries) for unrecoverable errors.
    Returns 500 for transient errors so Pub/Sub retries — capped by the
    dead letter topic configured on the subscription.
    """
    try:
        # Get the raw request body
        body = await request.body()

        # Parse the Pub/Sub push message
        push_message = json.loads(body)

        # Extract message data
        message_data = push_message.get("message", {})
        message_id = message_data.get("messageId", "unknown")
        publish_time = message_data.get("publishTime", "")

        # Cross-instance deduplication via Firestore — prevents duplicate
        # processing when Cloud Run cold start causes Pub/Sub to redeliver
        try:
            tracker = get_message_tracker()
            attempt = tracker.check_and_increment(message_id)
            if attempt == -1:
                logger.info(f"✅ Message {message_id} already processed — skipping duplicate")
                return Response(status_code=status.HTTP_204_NO_CONTENT)
            if attempt == 0:
                logger.info(f"⏳ Message {message_id} is already being processed — skipping duplicate delivery")
                return Response(status_code=status.HTTP_204_NO_CONTENT)
            if attempt > MAX_ATTEMPTS:
                logger.error(f"❌ Message {message_id} exceeded {MAX_ATTEMPTS} attempts — acknowledging")
                return Response(status_code=status.HTTP_204_NO_CONTENT)
            logger.info(f"📨 Received Pub/Sub push notification (attempt {attempt}/{MAX_ATTEMPTS})",
                        message_id=message_id, publish_time=publish_time)
        except Exception as tracker_err:
            # Fail closed: retries are safer than duplicate emails.
            logger.error(f"❌ Message tracker unavailable for {message_id}: {tracker_err}")
            raise RuntimeError(f"Message tracker unavailable for {message_id}") from tracker_err

        # Decode the message data
        encoded_data = message_data.get("data", "")
        if not encoded_data:
            logger.warning(f"⚠️ Message {message_id} has no data — acknowledging to prevent retry loop")
            return Response(status_code=status.HTTP_204_NO_CONTENT)

        # Decode base64 data
        try:
            decoded_data = base64.b64decode(encoded_data).decode("utf-8")
            client_data = json.loads(decoded_data)
        except (base64.binascii.Error, UnicodeDecodeError, json.JSONDecodeError) as e:
            # Unrecoverable — malformed message, retrying will never help
            logger.error(f"❌ Message {message_id} could not be decoded ({e}) — acknowledging to prevent retry loop")
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        
        # Extract the actual client data from the message structure
        if "data" in client_data:
            client_data = client_data["data"]
        
        # Log the received data structure
        logger.info(
            "📊 Processing client form data",
            message_id=message_id,
            data_fields=list(client_data.keys()) if isinstance(client_data, dict) else "not_dict"
        )
        
        # Add background task to process the message
        background_tasks.add_task(
            process_client_profile_generation,
            client_data,
            message_id,
            tracker
        )

        # Log successful message reception
        settings = get_settings()
        log_pubsub_message(
            topic=settings.pubsub_topic,
            message_id=message_id,
            status="received",
            background_task_added=True
        )

        return Response(status_code=status.HTTP_204_NO_CONTENT)
        
    except json.JSONDecodeError as e:
        # Malformed outer Pub/Sub envelope — unrecoverable
        logger.error(f"❌ Invalid JSON in request body: {str(e)} — acknowledging to prevent retry loop")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        logger.error(f"❌ Error processing Pub/Sub notification: {str(e)}")
        # Return 500 so Pub/Sub retries — capped by dead letter topic on the subscription
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


async def process_client_profile_generation(
    client_data: Dict[str, Any],
    message_id: str,
    tracker=None,
) -> None:
    """
    Background task to process client profile generation.
    
    This function:
    1. Processes the raw client data
    2. Converts it to structured format
    3. Generates AI profile
    4. Sends email report
    """
    try:
        logger.info(
            "🚀 Starting background profile generation",
            message_id=message_id,
            client_data_keys=list(client_data.keys())
        )

        # Use the callback pattern to process the message
        def profile_generation_callback(raw_client_data: RawClientData) -> None:
            """Callback function to handle profile generation."""
            from app.models.client_data import ClientFormData
            from app.services.genai_service import get_genai_service
            from app.services.email_service import get_email_service
            
            try:
                # Convert to structured data
                client_form_data = ClientFormData.from_raw_data(raw_client_data)
                
                logger.info(
                    "📋 Converted to structured data",
                    client_name=client_form_data.client_name,
                    project_type=client_form_data.project_type
                )
                
                # Generate AI profile
                genai_service = get_genai_service()
                profile = genai_service.generate_client_profile(client_form_data)
                
                logger.info(
                    "🤖 AI profile generated",
                    client_name=profile.client_name,
                    recommendations_count=len(profile.recommendations)
                )
                
                # Send email report
                email_service = get_email_service()
                email_status = email_service.send_profile_report(profile)
                
                logger.info(
                    "📧 Email report sent",
                    message_id=email_status.message_id,
                    recipient=email_status.recipient_email
                )
                
                # Mark processed so any cold-start retries are skipped
                if tracker:
                    try:
                        tracker.mark_processed(message_id)
                    except Exception as te:
                        logger.warning(f"⚠️ Failed to mark {message_id} as processed: {te}")

                # Log successful completion
                logger.info(
                    "✅ Profile generation completed successfully",
                    message_id=message_id,
                    client_name=profile.client_name,
                    email_message_id=email_status.message_id
                )
                
            except Exception as e:
                logger.error(
                    "❌ Error in profile generation callback",
                    message_id=message_id,
                    error=str(e)
                )
                raise
        
        # Process the message
        process_message_callback(client_data, message_id, profile_generation_callback)
        
    except Exception as e:
        logger.error(
            "❌ Background task failed",
            message_id=message_id,
            error=str(e)
        )
        # Note: In a production environment, you might want to implement
        # retry logic or dead letter queue handling here


@router.get("/health")
async def webhook_health_check() -> Dict[str, Any]:
    """Health check endpoint for webhooks."""
    return {
        "status": "healthy",
        "service": "webhooks",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "pubsub_push": "/webhooks/pubsub",
            "health": "/webhooks/health"
        }
    }


@router.post("/test")
async def test_webhook_processing(
    request: Request,
    background_tasks: BackgroundTasks
) -> JSONResponse:
    """
    Test endpoint for webhook processing.
    
    This endpoint allows testing the webhook processing logic
    without requiring actual Pub/Sub messages.
    """
    try:
        # Get test data from request body
        test_data = await request.json()
        
        # Generate a test message ID
        test_message_id = f"test_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(
            "🧪 Processing test webhook",
            message_id=test_message_id,
            test_data_keys=list(test_data.keys())
        )
        
        # Add background task to process the test data
        background_tasks.add_task(
            process_client_profile_generation,
            test_data,
            test_message_id
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Test data received and queued for processing",
                "message_id": test_message_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in request body")
    except Exception as e:
        logger.error(f"❌ Error in test webhook: {str(e)}")
        error_response = format_error_response(e)
        return JSONResponse(
            status_code=500,
            content=error_response
        )
