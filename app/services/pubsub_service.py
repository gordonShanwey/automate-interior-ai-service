"""Pub/Sub service for the Interior AI Service."""

import json
import base64
from typing import Dict, Any, Optional, Callable
from datetime import datetime

from google.cloud import pubsub_v1
from google.cloud.pubsub_v1.types import PubsubMessage

from app.config import get_settings
from app.models.client_data import RawClientData
from app.utils.errors import PubSubServiceError, handle_service_error
from app.utils.logging import log_pubsub_message, timed_operation, StructuredLogger
from app.utils.validators import validate_and_clean_data
from app.utils.logging import log_data_structure

logger = StructuredLogger("pubsub_service")


class PubSubService:
    """Google Cloud Pub/Sub service for processing client form messages."""
    
    def __init__(self):
        self.settings = get_settings()
        self.project_id = self.settings.google_cloud_project
        self.topic_name = self.settings.pubsub_topic
        self.subscription_name = self.settings.pubsub_subscription
        
        # Initialize Pub/Sub clients
        self._initialize_clients()
        
        logger.info(
            f"📨 Pub/Sub Service initialized",
            project_id=self.project_id,
            topic=self.topic_name,
            subscription=self.subscription_name
        )
    
    def _initialize_clients(self) -> None:
        """Initialize Pub/Sub publisher and subscriber clients."""
        try:
            # Initialize publisher client
            self.publisher = pubsub_v1.PublisherClient()
            self.topic_path = self.publisher.topic_path(self.project_id, self.topic_name)
            
            # Initialize subscriber client
            self.subscriber = pubsub_v1.SubscriberClient()
            self.subscription_path = self.subscriber.subscription_path(
                self.project_id, self.subscription_name
            )
            
            logger.info(f"✅ Pub/Sub clients initialized successfully")
            
        except Exception as e:
            raise PubSubServiceError(
                f"Failed to initialize Pub/Sub clients: {str(e)}",
                topic=self.topic_name,
                subscription=self.subscription_name
            )
    
    def process_client_form_message(self, message_data: Dict[str, Any], 
                                  message_id: Optional[str] = None) -> RawClientData:
        """Process incoming client form message with flexible validation."""
        with timed_operation("process_client_form_message", message_id=message_id):
            try:
                # Log the incoming message structure
                log_data_structure(message_data, "pubsub_message")
                
                # Validate and clean the data
                cleaned_data, validation_errors = validate_and_clean_data(message_data)
                
                # Log validation results
                if validation_errors:
                    logger.warning(
                        f"⚠️ Data validation warnings",
                        message_id=message_id,
                        validation_errors=validation_errors
                    )
                
                # Create RawClientData object
                raw_client_data = RawClientData(
                    raw_data=cleaned_data,
                    source=message_data.get("source", "pubsub"),
                    message_id=message_id
                )
                
                # Log the data structure for analysis
                raw_client_data.log_structure()
                
                # Log successful processing
                log_pubsub_message(
                    topic=self.topic_name,
                    message_id=message_id or "unknown",
                    status="processed",
                    field_count=len(cleaned_data),
                    validation_errors_count=len(validation_errors)
                )
                
                return raw_client_data
                
            except Exception as e:
                handle_service_error(
                    e, "PubSub", "process_client_form_message",
                    message_id=message_id
                )
    
    def publish_client_form_data(self, client_data: Dict[str, Any], 
                                source: str = "api") -> str:
        """Publish client form data to Pub/Sub topic."""
        with timed_operation("publish_client_form_data", source=source):
            try:
                # Add metadata to the message
                message_data = {
                    "data": client_data,
                    "source": source,
                    "timestamp": datetime.utcnow().isoformat(),
                    "version": "1.0"
                }
                
                # Convert to JSON
                message_json = json.dumps(message_data, ensure_ascii=False)
                message_bytes = message_json.encode("utf-8")
                
                # Publish message
                future = self.publisher.publish(
                    self.topic_path,
                    data=message_bytes,
                    source=source,
                    timestamp=message_data["timestamp"]
                )
                
                message_id = future.result()
                
                logger.info(
                    f"✅ Message published successfully",
                    message_id=message_id,
                    topic=self.topic_name,
                    source=source,
                    data_size=len(message_bytes)
                )
                
                return message_id
                
            except Exception as e:
                handle_service_error(
                    e, "PubSub", "publish_client_form_data",
                    source=source
                )
    
    def verify_message_authenticity(self, message: PubsubMessage) -> bool:
        """Verify message authenticity and integrity."""
        try:
            # Check if message has required attributes
            if not message.data:
                logger.warning("Message has no data")
                return False
            
            # Verify message format
            try:
                message_json = message.data.decode("utf-8")
                message_data = json.loads(message_json)
            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                logger.warning(f"Invalid message format: {str(e)}")
                return False
            
            # Check for required fields
            if "data" not in message_data:
                logger.warning("Message missing 'data' field")
                return False
            
            # Verify timestamp (optional)
            if "timestamp" in message_data:
                try:
                    timestamp = datetime.fromisoformat(message_data["timestamp"])
                    # Check if message is not too old (e.g., 24 hours)
                    if (datetime.utcnow() - timestamp).total_seconds() > 86400:
                        logger.warning("Message is too old")
                        return False
                except ValueError:
                    logger.warning("Invalid timestamp format")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error verifying message authenticity: {str(e)}")
            return False
    
    def decode_pubsub_message(self, message: PubsubMessage) -> Dict[str, Any]:
        """Decode and parse Pub/Sub message."""
        try:
            # Decode base64 data if needed
            if hasattr(message, 'data') and message.data:
                try:
                    # Try to decode as UTF-8 first
                    message_json = message.data.decode("utf-8")
                except UnicodeDecodeError:
                    # If that fails, try base64 decoding
                    decoded_data = base64.b64decode(message.data)
                    message_json = decoded_data.decode("utf-8")
                
                # Parse JSON
                message_data = json.loads(message_json)
                
                # Extract the actual client data
                if "data" in message_data:
                    return message_data["data"]
                else:
                    return message_data
            else:
                return {}
                
        except Exception as e:
            raise PubSubServiceError(
                f"Failed to decode Pub/Sub message: {str(e)}",
                message_id=getattr(message, 'message_id', 'unknown')
            )
    
    def create_subscription(self, subscription_name: Optional[str] = None) -> str:
        """Create a new subscription for the topic."""
        try:
            sub_name = subscription_name or self.subscription_name
            subscription_path = self.subscriber.subscription_path(self.project_id, sub_name)
            
            # Create subscription
            subscription = self.subscriber.create_subscription(
                name=subscription_path,
                topic=self.topic_path
            )
            
            logger.info(
                f"✅ Subscription created successfully",
                subscription_name=sub_name,
                subscription_path=subscription_path
            )
            
            return subscription_path
            
        except Exception as e:
            raise PubSubServiceError(
                f"Failed to create subscription: {str(e)}",
                topic=self.topic_name,
                subscription=sub_name
            )
    
    def delete_subscription(self, subscription_name: Optional[str] = None) -> None:
        """Delete a subscription."""
        try:
            sub_name = subscription_name or self.subscription_name
            subscription_path = self.subscriber.subscription_path(self.project_id, sub_name)
            
            # Delete subscription
            self.subscriber.delete_subscription(subscription=subscription_path)
            
            logger.info(
                f"✅ Subscription deleted successfully",
                subscription_name=sub_name
            )
            
        except Exception as e:
            raise PubSubServiceError(
                f"Failed to delete subscription: {str(e)}",
                subscription=sub_name
            )
    
    def get_subscription_info(self, subscription_name: Optional[str] = None) -> Dict[str, Any]:
        """Get information about a subscription."""
        try:
            sub_name = subscription_name or self.subscription_name
            subscription_path = self.subscriber.subscription_path(self.project_id, sub_name)
            
            # Get subscription
            subscription = self.subscriber.get_subscription(subscription=subscription_path)
            
            return {
                "name": subscription.name,
                "topic": subscription.topic,
                "ack_deadline_seconds": subscription.ack_deadline_seconds,
                "message_retention_duration": str(subscription.message_retention_duration),
                "retain_acked_messages": subscription.retain_acked_messages,
                "expiration_policy": str(subscription.expiration_policy),
                "filter": subscription.filter,
                "dead_letter_policy": str(subscription.dead_letter_policy) if subscription.dead_letter_policy else None
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "subscription_name": sub_name
            }
    
    def test_connection(self) -> Dict[str, Any]:
        """Test Pub/Sub service connection."""
        try:
            with timed_operation("test_pubsub_connection"):
                # Test topic access
                topic = self.publisher.get_topic(topic=self.topic_path)
                
                # Test subscription access
                subscription_info = self.get_subscription_info()
                
                return {
                    "status": "connected",
                    "topic": self.topic_name,
                    "subscription": self.subscription_name,
                    "topic_exists": topic is not None,
                    "subscription_info": subscription_info,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            return {
                "status": "error",
                "topic": self.topic_name,
                "subscription": self.subscription_name,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_message_count(self, subscription_name: Optional[str] = None) -> int:
        """Get the number of unacknowledged messages in a subscription."""
        try:
            sub_name = subscription_name or self.subscription_name
            subscription_path = self.subscriber.subscription_path(self.project_id, sub_name)
            
            # Get subscription stats
            request = pubsub_v1.GetSubscriptionRequest(subscription=subscription_path)
            subscription = self.subscriber.get_subscription(request=request)
            
            # Note: This is a simplified approach. For accurate counts,
            # you might need to use the Cloud Monitoring API
            return 0  # Placeholder - actual implementation would query monitoring API
            
        except Exception as e:
            logger.error(f"Failed to get message count: {str(e)}")
            return -1


# Global service instance
_pubsub_service_instance = None


def get_pubsub_service() -> PubSubService:
    """Get the global Pub/Sub service instance."""
    global _pubsub_service_instance
    if _pubsub_service_instance is None:
        _pubsub_service_instance = PubSubService()
    return _pubsub_service_instance


# Message processing callback for background tasks
def process_message_callback(message_data: Dict[str, Any], 
                           message_id: str,
                           callback: Callable[[RawClientData], None]) -> None:
    """Process a Pub/Sub message and call the provided callback."""
    try:
        # Get the Pub/Sub service instance
        pubsub_service = get_pubsub_service()
        
        # Process the message
        raw_client_data = pubsub_service.process_client_form_message(
            message_data, message_id
        )
        
        # Call the callback with the processed data
        callback(raw_client_data)
        
        logger.info(
            f"✅ Message processed successfully",
            message_id=message_id,
            callback_name=callback.__name__
        )
        
    except Exception as e:
        logger.error(
            f"❌ Failed to process message",
            message_id=message_id,
            error=str(e)
        )
        raise
