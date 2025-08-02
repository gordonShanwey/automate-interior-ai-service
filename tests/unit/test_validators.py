"""Tests for validators utility module."""

import pytest

from app.utils.validators import (
    validate_email,
    validate_phone,
    validate_budget_range,
    validate_project_type,
    validate_style_preference,
    validate_client_data,
    assess_data_quality,
    extract_structured_data,
    sanitize_data,
    validate_and_clean_data
)


class TestEmailValidation:
    """Test email validation functions."""

    def test_validate_email_valid(self):
        """Test email validation with valid email addresses."""
        assert validate_email("test@example.com") is True
        assert validate_email("user.name@domain.org") is True

    def test_validate_email_invalid(self):
        """Test email validation with invalid email addresses."""
        assert validate_email("") is False
        assert validate_email("not-an-email") is False
        assert validate_email("@domain.com") is False
        assert validate_email(None) is False


class TestPhoneValidation:
    """Test phone validation functions."""

    def test_validate_phone_valid(self):
        """Test phone validation with valid phone numbers."""
        assert validate_phone("+1234567890") is True
        assert validate_phone("555-123-4567") is True

    def test_validate_phone_invalid(self):
        """Test phone validation with invalid phone numbers."""
        assert validate_phone("") is False
        assert validate_phone("123") is False
        assert validate_phone("abc-def-ghij") is False
        assert validate_phone(None) is False


class TestBudgetValidation:
    """Test budget range validation functions."""

    def test_validate_budget_range_valid(self):
        """Test budget validation with valid ranges."""
        assert validate_budget_range("$5,000 - $10,000") is True
        assert validate_budget_range("10000-15000") is True

    def test_validate_budget_range_invalid(self):
        """Test budget validation with invalid ranges."""
        assert validate_budget_range("") is False
        assert validate_budget_range("free") is False
        assert validate_budget_range(None) is False


class TestProjectTypeValidation:
    """Test project type validation functions."""

    def test_validate_project_type_valid(self):
        """Test project type validation with valid types."""
        assert validate_project_type("Living Room Redesign") is True
        assert validate_project_type("Kitchen Renovation") is True

    def test_validate_project_type_invalid(self):
        """Test project type validation with invalid types."""
        assert validate_project_type("") is False
        assert validate_project_type("x") is False
        assert validate_project_type(None) is False


class TestStylePreferenceValidation:
    """Test style preference validation functions."""

    def test_validate_style_preference_valid(self):
        """Test style preference validation with valid preferences."""
        assert validate_style_preference("Modern") is True
        assert validate_style_preference("Traditional") is True

    def test_validate_style_preference_invalid(self):
        """Test style preference validation with invalid preferences."""
        assert validate_style_preference("") is False
        assert validate_style_preference("x") is False


class TestClientDataValidation:
    """Test complete client data validation."""

    def test_validate_client_data_valid(self):
        """Test client data validation with valid data."""
        valid_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "project_type": "Living Room Redesign"
        }
        
        is_valid, errors = validate_client_data(valid_data)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_client_data_invalid(self):
        """Test client data validation with invalid data."""
        invalid_data = {
            "name": "",
            "email": "invalid-email",
            "project_type": ""
        }
        
        is_valid, errors = validate_client_data(invalid_data)
        assert is_valid is False
        assert len(errors) > 0

    def test_validate_client_data_empty(self):
        """Test client data validation with empty data."""
        is_valid, errors = validate_client_data({})
        assert is_valid is False
        assert len(errors) > 0


class TestDataQuality:
    """Test data quality assessment functions."""

    def test_assess_data_quality(self):
        """Test data quality assessment."""
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1234567890"
        }
        
        quality = assess_data_quality(data)
        assert isinstance(quality, dict)
        assert "completeness_score" in quality

    def test_assess_data_quality_empty(self):
        """Test data quality assessment with empty data."""
        quality = assess_data_quality({})
        assert isinstance(quality, dict)
        assert quality["completeness_score"] == 0.0


class TestDataExtraction:
    """Test structured data extraction functions."""

    def test_extract_structured_data(self):
        """Test structured data extraction."""
        raw_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "random_field": "some value"
        }
        
        structured = extract_structured_data(raw_data)
        assert isinstance(structured, dict)
        assert "name" in structured
        assert "email" in structured

    def test_extract_structured_data_empty(self):
        """Test structured data extraction with empty data."""
        structured = extract_structured_data({})
        assert isinstance(structured, dict)


class TestDataSanitization:
    """Test data sanitization functions."""

    def test_sanitize_data(self):
        """Test data sanitization."""
        data = {
            "name": "  John Doe  ",
            "email": "JOHN@EXAMPLE.COM",
            "phone": " +1-234-567-8900 "
        }
        
        sanitized = sanitize_data(data)
        assert isinstance(sanitized, dict)
        assert sanitized["name"] == "John Doe"
        assert "@" in sanitized["email"]

    def test_sanitize_data_empty(self):
        """Test data sanitization with empty data."""
        sanitized = sanitize_data({})
        assert isinstance(sanitized, dict)


class TestValidateAndClean:
    """Test combined validation and cleaning functions."""

    def test_validate_and_clean_data_valid(self):
        """Test validation and cleaning with valid data."""
        data = {
            "name": "  John Doe  ",
            "email": "john@example.com",
            "project_type": "Living Room"
        }
        
        cleaned, errors = validate_and_clean_data(data)
        assert isinstance(cleaned, dict)
        assert isinstance(errors, list)
        assert len(errors) == 0

    def test_validate_and_clean_data_invalid(self):
        """Test validation and cleaning with invalid data."""
        data = {
            "name": "",
            "email": "invalid-email"
        }
        
        cleaned, errors = validate_and_clean_data(data)
        assert isinstance(cleaned, dict)
        assert isinstance(errors, list)
        assert len(errors) > 0

    def test_validate_and_clean_data_empty(self):
        """Test validation and cleaning with empty data."""
        cleaned, errors = validate_and_clean_data({})
        assert isinstance(cleaned, dict)
        assert isinstance(errors, list)