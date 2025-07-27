"""Webhook endpoints for the Interior AI Service."""

import json
import base64
from typing import Dict, Any
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Depends, status
from fastapi.responses import JSONResponse, Response

from app.models.client_data import RawClientData
from app.services.pubsub_service import get_pubsub_service, process_message_callback
from app.utils.errors import PubSubServiceError, format_error_response
from app.utils.logging import StructuredLogger, log_pubsub_message
from app.config import get_settings

logger = StructuredLogger("webhooks")
router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# Pub/Sub retry tracking
MAX_ENDPOINT_RETRIES = 3
endpoint_retry_counts = {}

def get_endpoint_retry_count(message_id: str) -> int:
    """Get current retry count for a message."""
    return endpoint_retry_counts.get(message_id, 0)

def increment_endpoint_retry_count(message_id: str) -> int:
    """Increment retry count for a message."""
    current = get_endpoint_retry_count(message_id)
    endpoint_retry_counts[message_id] = current + 1
    return endpoint_retry_counts[message_id]

def clear_endpoint_retry_count(message_id: str) -> None:
    """Clear retry count for a message."""
    endpoint_retry_counts.pop(message_id, None)


@router.post("/pubsub", status_code=status.HTTP_204_NO_CONTENT)
async def handle_pubsub_push_notification(
    request: Request,
    background_tasks: BackgroundTasks
) -> Response:
    """
    Handle Pub/Sub push notifications for client form data.
    
    This endpoint receives push notifications from Google Cloud Pub/Sub
    when new client form data is published to the configured topic.
    
    IMPORTANT: After MAX_ENDPOINT_RETRIES attempts, we ALWAYS acknowledge the message
    to prevent infinite loops, regardless of error type.
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
        
        # Check endpoint-level retry limit FIRST
        current_endpoint_retries = get_endpoint_retry_count(message_id)
        logger.info(f"Endpoint retry count for message {message_id}: {current_endpoint_retries}/{MAX_ENDPOINT_RETRIES}")
        
        if current_endpoint_retries >= MAX_ENDPOINT_RETRIES:
            logger.error(f"Message {message_id} exceeded endpoint retry limit ({MAX_ENDPOINT_RETRIES}), acknowledging to prevent infinite loop")
            clear_endpoint_retry_count(message_id)
            # ALWAYS acknowledge after max retries - prevents infinite loops
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        
        logger.info(
            f"📨 Received Pub/Sub push notification",
            message_id=message_id,
            publish_time=publish_time
        )
        
        # Decode the message data
        encoded_data = message_data.get("data", "")
        if not encoded_data:
            raise HTTPException(status_code=400, detail="No data in message")
        
        # Decode base64 data
        try:
            decoded_data = base64.b64decode(encoded_data).decode("utf-8")
            client_data = json.loads(decoded_data)
        except (base64.binascii.Error, UnicodeDecodeError, json.JSONDecodeError) as e:
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to decode message data: {str(e)}"
            )
        
        # Extract the actual client data from the message structure
        if "data" in client_data:
            client_data = client_data["data"]
        
        # Log the received data structure
        logger.info(
            f"📊 Processing client form data",
            message_id=message_id,
            data_fields=list(client_data.keys()) if isinstance(client_data, dict) else "not_dict"
        )
        
        # Add background task to process the message
        background_tasks.add_task(
            process_client_profile_generation,
            client_data,
            message_id
        )
        
        # Log successful message reception
        settings = get_settings()
        log_pubsub_message(
            topic=settings.pubsub_topic,
            message_id=message_id,
            status="received",
            background_task_added=True
        )
        
        # Clear endpoint retry counter on success
        clear_endpoint_retry_count(message_id)
        
        # Return 204 No Content to acknowledge the message
        return Response(status_code=status.HTTP_204_NO_CONTENT)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except json.JSONDecodeError as e:
        logger.error(f"❌ Invalid JSON in request body: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid JSON in request body")
    except Exception as e:
        logger.error(f"❌ Error processing Pub/Sub notification: {str(e)}")
        
        # Increment endpoint retry counter for ANY error
        new_endpoint_count = increment_endpoint_retry_count(message_id)
        logger.info(f"Incremented endpoint retry count for message {message_id} to {new_endpoint_count}/{MAX_ENDPOINT_RETRIES}")
        
        # If we've hit the limit, acknowledge to prevent infinite loops
        if new_endpoint_count >= MAX_ENDPOINT_RETRIES:
            logger.error(f"Message {message_id} reached endpoint retry limit, acknowledging to prevent infinite loop")
            clear_endpoint_retry_count(message_id)
            return Response(status_code=status.HTTP_204_NO_CONTENT)  # Acknowledge the message
        
        # Otherwise, return 500 for Pub/Sub retry
        logger.error(f"Returning 500 for message {message_id} retry (attempt {new_endpoint_count}/{MAX_ENDPOINT_RETRIES})")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed - retry attempt {new_endpoint_count}/{MAX_ENDPOINT_RETRIES}: {e}"
        )


async def process_client_profile_generation(
    client_data: Dict[str, Any],
    message_id: str
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
            f"🚀 Starting background profile generation",
            message_id=message_id,
            client_data_keys=list(client_data.keys())
        )
        
        # Process the message using Pub/Sub service
        pubsub_service = get_pubsub_service()
        
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
                    f"📋 Converted to structured data",
                    client_name=client_form_data.client_name,
                    project_type=client_form_data.project_type
                )
                
                # Generate AI profile
                genai_service = get_genai_service()
                profile = genai_service.generate_client_profile(client_form_data)
                
                logger.info(
                    f"🤖 AI profile generated",
                    client_name=profile.client_name,
                    recommendations_count=len(profile.recommendations)
                )
                
                # Send email report
                email_service = get_email_service()
                email_status = email_service.send_profile_report(profile)
                
                logger.info(
                    f"📧 Email report sent",
                    message_id=email_status.message_id,
                    recipient=email_status.recipient_email
                )
                
                # Log successful completion
                logger.info(
                    f"✅ Profile generation completed successfully",
                    message_id=message_id,
                    client_name=profile.client_name,
                    email_message_id=email_status.message_id
                )
                
            except Exception as e:
                logger.error(
                    f"❌ Error in profile generation callback",
                    message_id=message_id,
                    error=str(e)
                )
                raise
        
        # Process the message
        process_message_callback(client_data, message_id, profile_generation_callback)
        
    except Exception as e:
        logger.error(
            f"❌ Background task failed",
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
            f"🧪 Processing test webhook",
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
