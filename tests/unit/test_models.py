"""Unit tests for data models."""

import pytest
from datetime import datetime
from typing import Dict, Any

from app.models.client_data import RawClientData, ClientFormData


class TestRawClientData:
    """Test RawClientData model."""

    def test_raw_client_data_creation(self):
        """Test creating RawClientData instance."""
        raw_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "project_type": "Living Room",
        }
        
        client_data = RawClientData(
            raw_data=raw_data,
            source="test-form",
            message_id="test-msg-123"
        )
        
        assert client_data.raw_data == raw_data
        assert client_data.source == "test-form"
        assert client_data.message_id == "test-msg-123"
        assert isinstance(client_data.received_at, datetime)

    def test_raw_client_data_defaults(self):
        """Test RawClientData with default values."""
        raw_data = {"test": "data"}
        
        client_data = RawClientData(raw_data=raw_data)
        
        assert client_data.raw_data == raw_data
        assert client_data.source is None
        assert client_data.message_id is None
        assert isinstance(client_data.received_at, datetime)

    def test_log_structure(self, caplog):
        """Test log_structure method."""
        raw_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "project_type": "Living Room",
        }
        
        client_data = RawClientData(raw_data=raw_data)
        client_data.log_structure()
        
        # Check that structure was logged
        assert "Received client data structure" in caplog.text
        assert "name" in caplog.text
        assert "email" in caplog.text
        assert "project_type" in caplog.text

    def test_extract_basic_info_standard_fields(self):
        """Test extract_basic_info with standard field names."""
        raw_data = {
            "client_name": "John Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
            "project_type": "Living Room Redesign",
            "budget_range": "$10,000 - $15,000",
            "timeline": "3-6 months",
        }
        
        client_data = RawClientData(raw_data=raw_data)
        extracted = client_data.extract_basic_info()
        
        assert extracted["client_name"] == "John Doe"
        assert extracted["email"] == "john@example.com"
        assert extracted["phone"] == "+1234567890"
        assert extracted["project_type"] == "Living Room Redesign"
        assert extracted["budget_range"] == "$10,000 - $15,000"
        assert extracted["timeline"] == "3-6 months"

    def test_extract_basic_info_alternative_fields(self):
        """Test extract_basic_info with alternative field names."""
        raw_data = {
            "name": "Jane Smith",
            "email_address": "jane@example.com",
            "contact_phone": "+0987654321",
            "projectType": "Kitchen Remodel",
            "budgetRange": "$20,000 - $30,000",
            "completion_date": "6-12 months",
        }
        
        client_data = RawClientData(raw_data=raw_data)
        extracted = client_data.extract_basic_info()
        
        assert extracted["client_name"] == "Jane Smith"
        assert extracted["email"] == "jane@example.com"
        assert extracted["phone"] == "+0987654321"
        assert extracted["project_type"] == "Kitchen Remodel"
        assert extracted["budget_range"] == "$20,000 - $30,000"
        assert extracted["timeline"] == "6-12 months"

    def test_extract_basic_info_missing_fields(self):
        """Test extract_basic_info with missing fields."""
        raw_data = {
            "name": "Bob Wilson",
            "email": "bob@example.com",
            # Missing other fields
        }
        
        client_data = RawClientData(raw_data=raw_data)
        extracted = client_data.extract_basic_info()
        
        assert extracted["client_name"] == "Bob Wilson"
        assert extracted["email"] == "bob@example.com"
        assert "phone" not in extracted
        assert "project_type" not in extracted
        assert "budget_range" not in extracted
        assert "timeline" not in extracted

    def test_get_client_identifier_with_name(self):
        """Test get_client_identifier with client name."""
        raw_data = {"client_name": "John Doe", "email": "john@example.com"}
        
        client_data = RawClientData(raw_data=raw_data)
        identifier = client_data.get_client_identifier()
        
        assert identifier == "John Doe"

    def test_get_client_identifier_with_email(self):
        """Test get_client_identifier with email when name is missing."""
        raw_data = {"email": "john@example.com"}
        
        client_data = RawClientData(raw_data=raw_data)
        identifier = client_data.get_client_identifier()
        
        assert identifier == "john@example.com"

    def test_get_client_identifier_fallback(self):
        """Test get_client_identifier fallback to unknown."""
        raw_data = {"project_type": "Living Room"}
        
        client_data = RawClientData(raw_data=raw_data)
        identifier = client_data.get_client_identifier()
        
        assert identifier == "unknown_client"

    def test_validate_data_quality_complete(self):
        """Test validate_data_quality with complete data."""
        raw_data = {
            "client_name": "John Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
            "project_type": "Living Room Redesign",
            "budget_range": "$10,000 - $15,000",
            "timeline": "3-6 months",
        }
        
        client_data = RawClientData(raw_data=raw_data)
        quality = client_data.validate_data_quality()
        
        assert quality["total_fields"] == 6
        assert quality["required_fields_present"] >= 2  # name and email
        assert quality["data_quality_score"] > 0.5
        assert "missing_fields" in quality

    def test_validate_data_quality_minimal(self):
        """Test validate_data_quality with minimal data."""
        raw_data = {"email": "john@example.com"}
        
        client_data = RawClientData(raw_data=raw_data)
        quality = client_data.validate_data_quality()
        
        assert quality["total_fields"] == 1
        assert quality["required_fields_present"] == 1  # email
        assert quality["data_quality_score"] < 0.5
        assert "email" in quality["missing_fields"]


class TestClientFormData:
    """Test ClientFormData model."""

    def test_client_form_data_creation(self):
        """Test creating ClientFormData instance."""
        form_data = ClientFormData(
            client_name="John Doe",
            email="john@example.com",
            phone="+1234567890",
            project_type="Living Room Redesign",
            budget_range="$10,000 - $15,000",
            timeline="3-6 months",
            raw_data={"test": "data"}
        )
        
        assert form_data.client_name == "John Doe"
        assert form_data.email == "john@example.com"
        assert form_data.phone == "+1234567890"
        assert form_data.project_type == "Living Room Redesign"
        assert form_data.budget_range == "$10,000 - $15,000"
        assert form_data.timeline == "3-6 months"
        assert form_data.raw_data == {"test": "data"}
        assert isinstance(form_data.processed_at, datetime)

    def test_from_raw_data(self):
        """Test from_raw_data class method."""
        raw_data = {
            "client_name": "Jane Smith",
            "email": "jane@example.com",
            "phone": "+0987654321",
            "project_type": "Kitchen Remodel",
            "budget_range": "$20,000 - $30,000",
            "timeline": "6-12 months",
        }
        
        raw_client_data = RawClientData(raw_data=raw_data)
        form_data = ClientFormData.from_raw_data(raw_client_data)
        
        assert form_data.client_name == "Jane Smith"
        assert form_data.email == "jane@example.com"
        assert form_data.phone == "+0987654321"
        assert form_data.project_type == "Kitchen Remodel"
        assert form_data.budget_range == "$20,000 - $30,000"
        assert form_data.timeline == "6-12 months"
        assert form_data.raw_data == raw_data

    def test_from_raw_data_with_alternative_fields(self):
        """Test from_raw_data with alternative field names."""
        raw_data = {
            "name": "Bob Wilson",
            "email_address": "bob@example.com",
            "contact_phone": "+1122334455",
            "projectType": "Bedroom Design",
            "budgetRange": "$5,000 - $10,000",
            "completion_date": "2-4 months",
        }
        
        raw_client_data = RawClientData(raw_data=raw_data)
        form_data = ClientFormData.from_raw_data(raw_client_data)
        
        assert form_data.client_name == "Bob Wilson"
        assert form_data.email == "bob@example.com"
        assert form_data.phone == "+1122334455"
        assert form_data.project_type == "Bedroom Design"
        assert form_data.budget_range == "$5,000 - $10,000"
        assert form_data.timeline == "2-4 months"

    def test_to_genai_context_complete(self):
        """Test to_genai_context with complete data."""
        form_data = ClientFormData(
            client_name="John Doe",
            email="john@example.com",
            phone="+1234567890",
            project_type="Living Room Redesign",
            budget_range="$10,000 - $15,000",
            timeline="3-6 months",
            raw_data={
                "client_name": "John Doe",
                "email": "john@example.com",
                "phone": "+1234567890",
                "project_type": "Living Room Redesign",
                "budget_range": "$10,000 - $15,000",
                "timeline": "3-6 months",
                "room_size": "500 sq ft",
                "preferred_style": "Modern",
            }
        )
        
        context = form_data.to_genai_context()
        
        assert "Client: John Doe" in context
        assert "Project Type: Living Room Redesign" in context
        assert "Budget: $10,000 - $15,000" in context
        assert "Timeline: 3-6 months" in context
        assert "Room Size: 500 sq ft" in context
        assert "Preferred Style: Modern" in context

    def test_to_genai_context_minimal(self):
        """Test to_genai_context with minimal data."""
        form_data = ClientFormData(
            client_name="Jane Smith",
            raw_data={"client_name": "Jane Smith"}
        )
        
        context = form_data.to_genai_context()
        
        assert "Client: Jane Smith" in context
        assert "Project Type:" not in context
        assert "Budget:" not in context
        assert "Timeline:" not in context

    def test_to_genai_context_with_lists(self):
        """Test to_genai_context with list values."""
        form_data = ClientFormData(
            client_name="Alice Johnson",
            raw_data={
                "client_name": "Alice Johnson",
                "preferred_colors": ["blue", "green", "white"],
                "furniture_style": ["modern", "minimalist"],
            }
        )
        
        context = form_data.to_genai_context()
        
        assert "Preferred Colors: blue, green, white" in context
        assert "Furniture Style: modern, minimalist" in context

    def test_to_genai_context_with_non_string_values(self):
        """Test to_genai_context with non-string values."""
        form_data = ClientFormData(
            client_name="Bob Wilson",
            raw_data={
                "client_name": "Bob Wilson",
                "room_count": 3,
                "has_pets": True,
                "budget_amount": 15000.50,
            }
        )
        
        context = form_data.to_genai_context()
        
        assert "Room Count: 3" in context
        assert "Has Pets: True" in context
        assert "Budget Amount: 15000.5" in context 