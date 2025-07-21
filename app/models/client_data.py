"""Client form data models for the Interior AI Service."""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class RawClientData(BaseModel):
    """
    Flexible model for incoming client data - accepts any payload structure.
    Used for initial data acceptance and logging to understand real data patterns.
    """
    
    raw_data: Dict[str, Any] = Field(
        ..., 
        description="Raw incoming client form data - accepts any structure"
    )
    received_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when data was received"
    )
    source: Optional[str] = Field(
        None, 
        description="Source system or form identifier"
    )
    message_id: Optional[str] = Field(
        None,
        description="Pub/Sub message ID for tracking"
    )
    
    def log_structure(self) -> None:
        """Log the structure of incoming data for model development."""
        try:
            # Log basic structure information
            logger.info(f"📊 Received client data structure analysis:")
            logger.info(f"   📅 Received at: {self.received_at}")
            logger.info(f"   🏷️  Source: {self.source or 'unknown'}")
            logger.info(f"   🆔 Message ID: {self.message_id or 'unknown'}")
            logger.info(f"   📋 Field count: {len(self.raw_data)}")
            logger.info(f"   🔑 Field names: {list(self.raw_data.keys())}")
            
            # Log field types for analysis
            field_types = {}
            for key, value in self.raw_data.items():
                field_type = type(value).__name__
                if field_type not in field_types:
                    field_types[field_type] = []
                field_types[field_type].append(key)
            
            logger.info(f"   📊 Field types: {field_types}")
            
            # Log sample values (first 100 chars each)
            logger.info(f"   📝 Sample values:")
            for key, value in self.raw_data.items():
                if isinstance(value, str):
                    sample = value[:100] + "..." if len(value) > 100 else value
                else:
                    sample = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                logger.info(f"      {key}: {sample}")
                
        except Exception as e:
            logger.error(f"❌ Error logging data structure: {e}")
    
    def extract_basic_info(self) -> Dict[str, Any]:
        """
        Extract basic information with flexible field mapping.
        Handles common field name variations and nested structures.
        """
        extracted = {}
        
        # Common field mappings - adjust based on real data
        field_mappings = {
            'client_name': ['name', 'client_name', 'full_name', 'clientName', 'fullName', 'customer_name', 'customerName'],
            'email': ['email', 'email_address', 'contact_email', 'emailAddress', 'contactEmail'],
            'phone': ['phone', 'phone_number', 'contact_phone', 'mobile', 'phoneNumber', 'contactPhone', 'telephone'],
            'project_type': ['project_type', 'projectType', 'type', 'service_type', 'serviceType', 'project_category'],
            'budget_range': ['budget', 'budget_range', 'budgetRange', 'price_range', 'priceRange', 'budget_amount'],
            'timeline': ['timeline', 'timeframe', 'deadline', 'completion_date', 'completionDate', 'project_timeline'],
            'address': ['address', 'location', 'property_address', 'propertyAddress', 'home_address'],
            'room_count': ['rooms', 'room_count', 'number_of_rooms', 'roomCount', 'numberOfRooms'],
            'square_feet': ['square_feet', 'squareFeet', 'area', 'size', 'property_size', 'propertySize'],
            'style_preference': ['style', 'style_preference', 'design_style', 'stylePreference', 'designStyle', 'preferred_style'],
            'urgency': ['urgency', 'priority', 'timeline_urgency', 'project_priority'],
        }
        
        # Extract fields using mappings
        for standard_key, possible_keys in field_mappings.items():
            for key in possible_keys:
                if key in self.raw_data:
                    value = self.raw_data[key]
                    # Handle nested structures
                    if isinstance(value, dict) and 'value' in value:
                        extracted[standard_key] = value['value']
                    elif isinstance(value, list) and len(value) > 0:
                        extracted[standard_key] = value[0] if isinstance(value[0], str) else str(value[0])
                    else:
                        extracted[standard_key] = value
                    break
        
        # Add any other fields from raw data that weren't mapped
        mapped_keys = set()
        for keys in field_mappings.values():
            mapped_keys.update(keys)
        
        unmapped_fields = {}
        for key, value in self.raw_data.items():
            if key not in mapped_keys:
                if isinstance(value, (str, int, float, bool)):
                    unmapped_fields[key] = value
                elif isinstance(value, list):
                    unmapped_fields[key] = str(value)
                elif isinstance(value, dict):
                    unmapped_fields[key] = str(value)
        
        if unmapped_fields:
            extracted['additional_fields'] = unmapped_fields
            logger.info(f"🔍 Found unmapped fields: {list(unmapped_fields.keys())}")
        
        return extracted
    
    def get_client_identifier(self) -> str:
        """Get a client identifier for logging and tracking."""
        extracted = self.extract_basic_info()
        
        # Try to get a meaningful identifier
        if extracted.get('client_name'):
            return extracted['client_name']
        elif extracted.get('email'):
            return extracted['email']
        elif self.message_id:
            return f"message_{self.message_id[:8]}"
        else:
            return f"client_{self.received_at.strftime('%Y%m%d_%H%M%S')}"
    
    def validate_data_quality(self) -> Dict[str, Any]:
        """Assess data quality and completeness."""
        extracted = self.extract_basic_info()
        
        quality_report = {
            'total_fields': len(self.raw_data),
            'mapped_fields': len([k for k in extracted.keys() if k != 'additional_fields']),
            'unmapped_fields': len(extracted.get('additional_fields', {})),
            'missing_critical_fields': [],
            'data_types': {},
            'quality_score': 0
        }
        
        # Check for critical fields
        critical_fields = ['client_name', 'email', 'project_type']
        for field in critical_fields:
            if not extracted.get(field):
                quality_report['missing_critical_fields'].append(field)
        
        # Analyze data types
        for key, value in self.raw_data.items():
            field_type = type(value).__name__
            if field_type not in quality_report['data_types']:
                quality_report['data_types'][field_type] = 0
            quality_report['data_types'][field_type] += 1
        
        # Calculate quality score
        mapped_ratio = quality_report['mapped_fields'] / max(quality_report['total_fields'], 1)
        critical_ratio = (len(critical_fields) - len(quality_report['missing_critical_fields'])) / len(critical_fields)
        quality_report['quality_score'] = (mapped_ratio + critical_ratio) / 2
        
        return quality_report


# TODO: Create proper ClientFormData model after analyzing real data patterns
# This will be implemented after we receive actual client form submissions
class ClientFormData(BaseModel):
    """
    Structured model for validated client data.
    Will be implemented after analyzing real incoming data patterns.
    """
    client_name: Optional[str] = Field(None, description="Client name")
    email: Optional[str] = Field(None, description="Client email")
    phone: Optional[str] = Field(None, description="Client phone")
    project_type: Optional[str] = Field(None, description="Project type")
    budget_range: Optional[str] = Field(None, description="Budget range")
    timeline: Optional[str] = Field(None, description="Project timeline")
    address: Optional[str] = Field(None, description="Property address")
    room_count: Optional[str] = Field(None, description="Number of rooms")
    square_feet: Optional[str] = Field(None, description="Property size")
    style_preference: Optional[str] = Field(None, description="Design style preference")
    urgency: Optional[str] = Field(None, description="Project urgency")
    raw_data: Dict[str, Any] = Field(..., description="Original raw data")
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    
    @classmethod
    def from_raw_data(cls, raw_client_data: RawClientData) -> 'ClientFormData':
        """Create structured data from raw client data."""
        extracted = raw_client_data.extract_basic_info()
        
        return cls(
            client_name=extracted.get('client_name'),
            email=extracted.get('email'),
            phone=extracted.get('phone'),
            project_type=extracted.get('project_type'),
            budget_range=extracted.get('budget_range'),
            timeline=extracted.get('timeline'),
            address=extracted.get('address'),
            room_count=extracted.get('room_count'),
            square_feet=extracted.get('square_feet'),
            style_preference=extracted.get('style_preference'),
            urgency=extracted.get('urgency'),
            raw_data=raw_client_data.raw_data,
        )
    
    def to_genai_context(self) -> str:
        """Convert to context string for Gen AI processing."""
        context_parts = []
        
        # Add basic client information
        if self.client_name:
            context_parts.append(f"Client: {self.client_name}")
        if self.email:
            context_parts.append(f"Email: {self.email}")
        if self.phone:
            context_parts.append(f"Phone: {self.phone}")
        
        # Add project details
        if self.project_type:
            context_parts.append(f"Project Type: {self.project_type}")
        if self.budget_range:
            context_parts.append(f"Budget: {self.budget_range}")
        if self.timeline:
            context_parts.append(f"Timeline: {self.timeline}")
        
        # Add property details
        if self.address:
            context_parts.append(f"Property Address: {self.address}")
        if self.room_count:
            context_parts.append(f"Number of Rooms: {self.room_count}")
        if self.square_feet:
            context_parts.append(f"Property Size: {self.square_feet}")
        
        # Add preferences
        if self.style_preference:
            context_parts.append(f"Style Preference: {self.style_preference}")
        if self.urgency:
            context_parts.append(f"Project Urgency: {self.urgency}")
        
        # Add any additional fields from raw data
        additional_fields = self.raw_data.get('additional_fields', {})
        for key, value in additional_fields.items():
            if isinstance(value, (str, int, float, bool)):
                context_parts.append(f"{key.replace('_', ' ').title()}: {value}")
        
        return "\n".join(context_parts)
