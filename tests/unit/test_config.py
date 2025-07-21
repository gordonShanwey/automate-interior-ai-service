"""Unit tests for configuration module."""

import pytest
from unittest.mock import patch, MagicMock
from pydantic import ValidationError

from app.config import get_settings, validate_configuration, Settings


class TestSettings:
    """Test Settings model."""

    def test_settings_default_values(self):
        """Test that Settings has expected default values."""
        with patch.dict("os.environ", {}, clear=True):
            settings = Settings()
            
            assert settings.app_name == "Interior AI Service"
            assert settings.app_version == "0.1.0"
            assert settings.environment == "development"
            assert settings.debug is True
            assert settings.log_level == "INFO"

    def test_settings_from_environment(self):
        """Test that Settings reads from environment variables."""
        env_vars = {
            "APP_NAME": "Test Service",
            "APP_VERSION": "1.0.0",
            "ENVIRONMENT": "production",
            "DEBUG": "false",
            "LOG_LEVEL": "ERROR",
            "GOOGLE_CLOUD_PROJECT": "test-project",
            "VERTEX_AI_LOCATION": "us-central1",
            "GENAI_MODEL": "gemini-1.5-pro",
            "PUBSUB_TOPIC": "test-topic",
            "PUBSUB_SUBSCRIPTION": "test-subscription",
            "SMTP_SERVER": "smtp.test.com",
            "SMTP_PORT": "587",
            "SMTP_USERNAME": "test@test.com",
            "SMTP_PASSWORD": "test-password",
            "DESIGNER_EMAIL": "designer@test.com",
        }
        
        with patch.dict("os.environ", env_vars, clear=True):
            settings = Settings()
            
            assert settings.app_name == "Test Service"
            assert settings.app_version == "1.0.0"
            assert settings.environment == "production"
            assert settings.debug is False
            assert settings.log_level == "ERROR"
            assert settings.google_cloud_project == "test-project"
            assert settings.vertex_ai_location == "us-central1"
            assert settings.genai_model == "gemini-1.5-pro"
            assert settings.pubsub_topic == "test-topic"
            assert settings.pubsub_subscription == "test-subscription"
            assert settings.smtp_server == "smtp.test.com"
            assert settings.smtp_port == 587
            assert settings.smtp_username == "test@test.com"
            assert settings.smtp_password == "test-password"
            assert settings.designer_email == "designer@test.com"

    def test_settings_validation_environment(self):
        """Test environment validation."""
        with patch.dict("os.environ", {"ENVIRONMENT": "invalid"}, clear=True):
            with pytest.raises(ValidationError):
                Settings()

    def test_settings_validation_log_level(self):
        """Test log level validation."""
        with patch.dict("os.environ", {"LOG_LEVEL": "INVALID"}, clear=True):
            with pytest.raises(ValidationError):
                Settings()

    def test_settings_validation_smtp_port(self):
        """Test SMTP port validation."""
        with patch.dict("os.environ", {"SMTP_PORT": "invalid"}, clear=True):
            with pytest.raises(ValidationError):
                Settings()

    def test_settings_validation_email(self):
        """Test email validation."""
        with patch.dict("os.environ", {"DESIGNER_EMAIL": "invalid-email"}, clear=True):
            with pytest.raises(ValidationError):
                Settings()

    def test_settings_model_config(self):
        """Test Settings model configuration."""
        settings = Settings()
        
        # Test that model_config is set correctly
        assert hasattr(settings, "model_config")
        assert settings.model_config["env_file"] == ".env.local"
        assert settings.model_config["env_file_encoding"] == "utf-8"
        assert settings.model_config["case_sensitive"] is False
        assert settings.model_config["extra"] == "ignore"


class TestGetSettings:
    """Test get_settings function."""

    def test_get_settings_returns_settings_instance(self):
        """Test that get_settings returns a Settings instance."""
        settings = get_settings()
        
        assert isinstance(settings, Settings)

    def test_get_settings_caching(self):
        """Test that get_settings caches the result."""
        settings1 = get_settings()
        settings2 = get_settings()
        
        # Should be the same instance due to caching
        assert settings1 is settings2

    def test_get_settings_with_environment(self):
        """Test get_settings with environment variables."""
        env_vars = {
            "APP_NAME": "Cached Test Service",
            "ENVIRONMENT": "test",
        }
        
        with patch.dict("os.environ", env_vars, clear=True):
            settings = get_settings()
            
            assert settings.app_name == "Cached Test Service"
            assert settings.environment == "test"


class TestValidateConfiguration:
    """Test validate_configuration function."""

    def test_validate_configuration_success(self):
        """Test successful configuration validation."""
        with patch("app.config.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.google_cloud_project = "test-project"
            mock_settings.vertex_ai_location = "us-central1"
            mock_settings.pubsub_topic = "test-topic"
            mock_settings.pubsub_subscription = "test-subscription"
            mock_settings.smtp_server = "smtp.test.com"
            mock_settings.smtp_port = 587
            mock_settings.smtp_username = "test@test.com"
            mock_settings.smtp_password = "test-password"
            mock_settings.designer_email = "designer@test.com"
            
            mock_get_settings.return_value = mock_settings
            
            result = validate_configuration()
            
            assert result is True

    def test_validate_configuration_missing_google_cloud_project(self):
        """Test configuration validation with missing Google Cloud project."""
        with patch("app.config.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.google_cloud_project = ""
            mock_get_settings.return_value = mock_settings
            
            result = validate_configuration()
            
            assert result is False

    def test_validate_configuration_missing_vertex_ai_location(self):
        """Test configuration validation with missing Vertex AI location."""
        with patch("app.config.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.google_cloud_project = "test-project"
            mock_settings.vertex_ai_location = ""
            mock_get_settings.return_value = mock_settings
            
            result = validate_configuration()
            
            assert result is False

    def test_validate_configuration_missing_pubsub_topic(self):
        """Test configuration validation with missing Pub/Sub topic."""
        with patch("app.config.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.google_cloud_project = "test-project"
            mock_settings.vertex_ai_location = "us-central1"
            mock_settings.pubsub_topic = ""
            mock_get_settings.return_value = mock_settings
            
            result = validate_configuration()
            
            assert result is False

    def test_validate_configuration_missing_smtp_config(self):
        """Test configuration validation with missing SMTP configuration."""
        with patch("app.config.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.google_cloud_project = "test-project"
            mock_settings.vertex_ai_location = "us-central1"
            mock_settings.pubsub_topic = "test-topic"
            mock_settings.smtp_server = ""
            mock_get_settings.return_value = mock_settings
            
            result = validate_configuration()
            
            assert result is False


class TestFieldValidators:
    """Test field validators."""

    def test_validate_environment_valid_values(self):
        """Test environment validation with valid values."""
        valid_environments = ["development", "staging", "production", "test"]
        
        for env in valid_environments:
            with patch.dict("os.environ", {"ENVIRONMENT": env}, clear=True):
                settings = Settings()
                assert settings.environment == env

    def test_validate_environment_invalid_value(self):
        """Test environment validation with invalid value."""
        with patch.dict("os.environ", {"ENVIRONMENT": "invalid"}, clear=True):
            with pytest.raises(ValidationError):
                Settings()

    def test_validate_log_level_valid_values(self):
        """Test log level validation with valid values."""
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        for level in valid_log_levels:
            with patch.dict("os.environ", {"LOG_LEVEL": level}, clear=True):
                settings = Settings()
                assert settings.log_level == level

    def test_validate_log_level_invalid_value(self):
        """Test log level validation with invalid value."""
        with patch.dict("os.environ", {"LOG_LEVEL": "INVALID"}, clear=True):
            with pytest.raises(ValidationError):
                Settings()

    def test_validate_smtp_port_valid_values(self):
        """Test SMTP port validation with valid values."""
        valid_ports = [25, 465, 587, 2525]
        
        for port in valid_ports:
            with patch.dict("os.environ", {"SMTP_PORT": str(port)}, clear=True):
                settings = Settings()
                assert settings.smtp_port == port

    def test_validate_smtp_port_invalid_value(self):
        """Test SMTP port validation with invalid value."""
        with patch.dict("os.environ", {"SMTP_PORT": "99999"}, clear=True):
            with pytest.raises(ValidationError):
                Settings() 