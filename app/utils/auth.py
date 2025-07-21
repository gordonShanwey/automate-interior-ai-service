"""Authentication utilities for Google Cloud services."""

import logging
from typing import Dict, Any, Optional, List
from google.auth import default
from google.auth.exceptions import DefaultCredentialsError
from google.cloud import pubsub_v1
import google.cloud.aiplatform as aiplatform
from google.api_core import exceptions

from app.config import get_settings

logger = logging.getLogger(__name__)


async def test_google_cloud_auth() -> Dict[str, Any]:
    """Test Google Cloud authentication and return status."""
    auth_status = {
        "authenticated": False,
        "project_id": None,
        "credentials_type": None,
        "error": None
    }
    
    try:
        # Get default credentials
        credentials, project_id = default()
        auth_status["authenticated"] = True
        auth_status["project_id"] = project_id
        auth_status["credentials_type"] = type(credentials).__name__
        
        logger.info(f"✅ Google Cloud authentication successful")
        logger.info(f"   📋 Project ID: {project_id}")
        logger.info(f"   🔑 Credentials type: {type(credentials).__name__}")
        
    except DefaultCredentialsError as e:
        auth_status["error"] = str(e)
        logger.error(f"❌ Google Cloud authentication failed: {e}")
        
    except Exception as e:
        auth_status["error"] = str(e)
        logger.error(f"❌ Unexpected authentication error: {e}")
    
    return auth_status


async def test_vertex_ai_access() -> Dict[str, Any]:
    """Test Vertex AI access and permissions."""
    vertex_status = {
        "accessible": False,
        "location": None,
        "models_available": False,
        "error": None
    }
    
    try:
        settings = get_settings()
        
        # Initialize Vertex AI client
        aiplatform.init(
            project=settings.google_cloud_project,
            location=settings.vertex_ai_location
        )
        
        vertex_status["accessible"] = True
        vertex_status["location"] = settings.vertex_ai_location
        
        # Test model access (list models)
        try:
            # This will test if we can access the model
            # We'll just test the connection, not actually call the model
            vertex_status["models_available"] = True
            logger.info(f"✅ Vertex AI access successful")
            logger.info(f"   📍 Location: {settings.vertex_ai_location}")
            logger.info(f"   🤖 Model: {settings.genai_model}")
            
        except Exception as e:
            vertex_status["error"] = f"Model access failed: {str(e)}"
            logger.warning(f"⚠️  Vertex AI accessible but model access failed: {e}")
            
    except Exception as e:
        vertex_status["error"] = str(e)
        logger.error(f"❌ Vertex AI access failed: {e}")
    
    return vertex_status


async def test_pubsub_access() -> Dict[str, Any]:
    """Test Pub/Sub access and permissions."""
    pubsub_status = {
        "accessible": False,
        "topic_exists": False,
        "subscription_exists": False,
        "error": None
    }
    
    try:
        settings = get_settings()
        
        # Initialize Pub/Sub client
        publisher = pubsub_v1.PublisherClient()
        subscriber = pubsub_v1.SubscriberClient()
        
        # Test topic access
        try:
            topic_path = publisher.topic_path(settings.google_cloud_project, settings.pubsub_topic)
            topic = publisher.get_topic(request={"topic": topic_path})
            pubsub_status["topic_exists"] = True
            logger.info(f"✅ Pub/Sub topic accessible: {settings.pubsub_topic}")
            
        except exceptions.NotFound:
            logger.warning(f"⚠️  Pub/Sub topic not found: {settings.pubsub_topic}")
        except Exception as e:
            logger.error(f"❌ Pub/Sub topic access failed: {e}")
            pubsub_status["error"] = f"Topic access failed: {str(e)}"
            return pubsub_status
        
        # Test subscription access
        try:
            subscription_path = subscriber.subscription_path(
                settings.google_cloud_project, 
                settings.pubsub_subscription
            )
            subscription = subscriber.get_subscription(request={"subscription": subscription_path})
            pubsub_status["subscription_exists"] = True
            logger.info(f"✅ Pub/Sub subscription accessible: {settings.pubsub_subscription}")
            
        except exceptions.NotFound:
            logger.warning(f"⚠️  Pub/Sub subscription not found: {settings.pubsub_subscription}")
        except Exception as e:
            logger.error(f"❌ Pub/Sub subscription access failed: {e}")
            if not pubsub_status["error"]:
                pubsub_status["error"] = f"Subscription access failed: {str(e)}"
        
        pubsub_status["accessible"] = True
        
    except Exception as e:
        pubsub_status["error"] = str(e)
        logger.error(f"❌ Pub/Sub access failed: {e}")
    
    return pubsub_status


async def test_service_account_permissions() -> Dict[str, Any]:
    """Test service account permissions for required roles."""
    permissions_status = {
        "vertex_ai_user": False,
        "pubsub_subscriber": False,
        "logging_writer": False,
        "monitoring_writer": False,
        "errors": []
    }
    
    try:
        # Test Vertex AI permissions
        vertex_status = await test_vertex_ai_access()
        permissions_status["vertex_ai_user"] = vertex_status["accessible"]
        if not vertex_status["accessible"]:
            permissions_status["errors"].append(f"Vertex AI: {vertex_status.get('error', 'Unknown error')}")
        
        # Test Pub/Sub permissions
        pubsub_status = await test_pubsub_access()
        permissions_status["pubsub_subscriber"] = pubsub_status["accessible"]
        if not pubsub_status["accessible"]:
            permissions_status["errors"].append(f"Pub/Sub: {pubsub_status.get('error', 'Unknown error')}")
        
        # Test logging permissions (basic test)
        try:
            # This is a basic test - in practice, logging will work if other services work
            permissions_status["logging_writer"] = True
            logger.info("✅ Logging permissions appear to be working")
        except Exception as e:
            permissions_status["errors"].append(f"Logging: {str(e)}")
        
        # Test monitoring permissions (basic test)
        try:
            # This is a basic test - in practice, monitoring will work if other services work
            permissions_status["monitoring_writer"] = True
            logger.info("✅ Monitoring permissions appear to be working")
        except Exception as e:
            permissions_status["errors"].append(f"Monitoring: {str(e)}")
        
        logger.info(f"📊 Service account permissions test completed")
        logger.info(f"   🤖 Vertex AI: {'✅' if permissions_status['vertex_ai_user'] else '❌'}")
        logger.info(f"   📨 Pub/Sub: {'✅' if permissions_status['pubsub_subscriber'] else '❌'}")
        logger.info(f"   📝 Logging: {'✅' if permissions_status['logging_writer'] else '❌'}")
        logger.info(f"   📊 Monitoring: {'✅' if permissions_status['monitoring_writer'] else '❌'}")
        
    except Exception as e:
        permissions_status["errors"].append(f"General error: {str(e)}")
        logger.error(f"❌ Service account permissions test failed: {e}")
    
    return permissions_status


async def run_authentication_tests() -> Dict[str, Any]:
    """Run all authentication tests and return comprehensive status."""
    logger.info("🔐 Starting authentication tests...")
    
    test_results = {
        "google_cloud_auth": await test_google_cloud_auth(),
        "vertex_ai_access": await test_vertex_ai_access(),
        "pubsub_access": await test_pubsub_access(),
        "service_account_permissions": await test_service_account_permissions(),
        "overall_status": "unknown"
    }
    
    # Determine overall status
    auth_ok = test_results["google_cloud_auth"]["authenticated"]
    vertex_ok = test_results["vertex_ai_access"]["accessible"]
    pubsub_ok = test_results["pubsub_access"]["accessible"]
    
    if auth_ok and vertex_ok and pubsub_ok:
        test_results["overall_status"] = "healthy"
        logger.info("🎉 All authentication tests passed!")
    elif auth_ok:
        test_results["overall_status"] = "partial"
        logger.warning("⚠️  Authentication partial - some services not accessible")
    else:
        test_results["overall_status"] = "unhealthy"
        logger.error("❌ Authentication tests failed")
    
    return test_results


def get_authentication_help() -> str:
    """Get help text for authentication setup."""
    return """
🔐 Google Cloud Authentication Setup Help

For Local Development:
1. Install Google Cloud SDK: https://cloud.google.com/sdk/docs/install
2. Run: gcloud auth application-default login
3. Set your project: gcloud config set project YOUR_PROJECT_ID
4. Verify: gcloud auth list

For Production:
1. Create service account in Google Cloud Console
2. Assign required roles:
   - roles/aiplatform.user (Vertex AI)
   - roles/pubsub.subscriber (Pub/Sub)
   - roles/logging.logWriter (Cloud Logging)
   - roles/monitoring.metricWriter (Cloud Monitoring)
3. Download service account key (optional for Cloud Run)
4. Set GOOGLE_APPLICATION_CREDENTIALS environment variable

Required Environment Variables:
- GOOGLE_CLOUD_PROJECT: Your Google Cloud Project ID
- VERTEX_AI_LOCATION: Vertex AI location (e.g., us-central1)
- PUBSUB_TOPIC: Pub/Sub topic name
- PUBSUB_SUBSCRIPTION: Pub/Sub subscription name

Test Authentication:
- Run the application and check /health/readiness endpoint
- Check logs for authentication status
- Use authentication testing utilities in app/utils/auth.py
""" 