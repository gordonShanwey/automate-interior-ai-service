"""Validation utilities for the Interior AI Service."""

import re
from typing import Dict, Any, Optional, List, Union, Tuple
from datetime import datetime

from app.utils.errors import DataValidationError


def validate_email(email: str) -> bool:
    """Validate email format."""
    if not email:
        return False
    
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """Validate phone number format."""
    if not phone:
        return False
    
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Check if it's a valid length (7-15 digits)
    return 7 <= len(digits_only) <= 15


def validate_budget_range(budget: str) -> bool:
    """Validate budget range format."""
    if not budget:
        return False
    
    # Common budget patterns
    patterns = [
        r'^\$\d+-\d+$',  # $1000-5000
        r'^\$\d+,\d+-\d+,\d+$',  # $1,000-5,000
        r'^\d+-\d+$',  # 1000-5000
        r'^\$\d+$',  # $5000
        r'^\d+$',  # 5000
        r'^\$\d+,\d+$',  # $5,000
    ]
    
    return any(re.match(pattern, budget) for pattern in patterns)


def validate_project_type(project_type: str) -> bool:
    """Validate project type."""
    if not project_type:
        return False
    
    # Common interior design project types
    valid_types = [
        'living room', 'bedroom', 'kitchen', 'bathroom', 'dining room',
        'home office', 'basement', 'attic', 'garage', 'outdoor space',
        'entire home', 'apartment', 'condo', 'studio', 'loft',
        'commercial space', 'retail space', 'office space', 'restaurant',
        'hotel room', 'vacation home', 'renovation', 'new construction'
    ]
    
    return project_type.lower() in valid_types


def validate_style_preference(style: str) -> bool:
    """Validate design style preference."""
    if not style:
        return False
    
    # Common design styles
    valid_styles = [
        'modern', 'contemporary', 'traditional', 'classic', 'minimalist',
        'scandinavian', 'industrial', 'rustic', 'farmhouse', 'coastal',
        'bohemian', 'mid-century modern', 'art deco', 'victorian',
        'mediterranean', 'asian', 'tropical', 'eclectic', 'luxury',
        'budget-friendly', 'sustainable', 'smart home'
    ]
    
    return style.lower() in valid_styles


def detect_field_type(value: Any) -> str:
    """Detect the type of a field value."""
    if value is None:
        return "null"
    elif isinstance(value, str):
        # Try to detect specific string types
        if validate_email(value):
            return "email"
        elif validate_phone(value):
            return "phone"
        elif validate_budget_range(value):
            return "budget"
        elif validate_project_type(value):
            return "project_type"
        elif validate_style_preference(value):
            return "style"
        elif re.match(r'^\d+$', value):
            return "integer_string"
        elif re.match(r'^\d+\.\d+$', value):
            return "float_string"
        else:
            return "string"
    elif isinstance(value, int):
        return "integer"
    elif isinstance(value, float):
        return "float"
    elif isinstance(value, bool):
        return "boolean"
    elif isinstance(value, list):
        return "array"
    elif isinstance(value, dict):
        return "object"
    else:
        return "unknown"


def convert_field_value(value: Any, target_type: str) -> Any:
    """Convert field value to target type."""
    if value is None:
        return None
    
    try:
        if target_type == "string":
            return str(value)
        elif target_type == "integer":
            return int(value)
        elif target_type == "float":
            return float(value)
        elif target_type == "boolean":
            if isinstance(value, str):
                return value.lower() in ['true', '1', 'yes', 'on']
            return bool(value)
        elif target_type == "email":
            if isinstance(value, str) and validate_email(value):
                return value.lower()
            raise ValueError("Invalid email format")
        elif target_type == "phone":
            if isinstance(value, str) and validate_phone(value):
                return value
            raise ValueError("Invalid phone format")
        else:
            return value
    except (ValueError, TypeError) as e:
        raise DataValidationError(f"Failed to convert {value} to {target_type}: {str(e)}")


def assess_data_quality(data: Dict[str, Any]) -> Dict[str, Any]:
    """Assess the quality of incoming data."""
    quality_report = {
        "total_fields": len(data),
        "field_types": {},
        "missing_critical_fields": [],
        "invalid_fields": [],
        "quality_score": 0.0,
        "recommendations": []
    }
    
    # Define critical fields
    critical_fields = ['client_name', 'email', 'project_type']
    field_mappings = {
        'client_name': ['name', 'client_name', 'full_name', 'clientName', 'fullName'],
        'email': ['email', 'email_address', 'contact_email', 'emailAddress'],
        'project_type': ['project_type', 'projectType', 'type', 'service_type']
    }
    
    # Analyze field types
    for key, value in data.items():
        field_type = detect_field_type(value)
        if field_type not in quality_report["field_types"]:
            quality_report["field_types"][field_type] = []
        quality_report["field_types"][field_type].append(key)
    
    # Check for critical fields
    found_critical_fields = set()
    for critical_field, possible_names in field_mappings.items():
        found = False
        for possible_name in possible_names:
            if possible_name in data:
                found_critical_fields.add(critical_field)
                found = True
                break
        if not found:
            quality_report["missing_critical_fields"].append(critical_field)
    
    # Check for invalid fields
    for key, value in data.items():
        if isinstance(value, str):
            if key.lower() in ['email', 'email_address'] and not validate_email(value):
                quality_report["invalid_fields"].append(f"{key}: invalid email format")
            elif key.lower() in ['phone', 'phone_number'] and not validate_phone(value):
                quality_report["invalid_fields"].append(f"{key}: invalid phone format")
    
    # Calculate quality score
    critical_ratio = len(found_critical_fields) / len(critical_fields)
    valid_ratio = 1.0 - (len(quality_report["invalid_fields"]) / max(len(data), 1))
    quality_report["quality_score"] = (critical_ratio + valid_ratio) / 2
    
    # Generate recommendations
    if quality_report["missing_critical_fields"]:
        quality_report["recommendations"].append(
            f"Add missing critical fields: {', '.join(quality_report['missing_critical_fields'])}"
        )
    
    if quality_report["invalid_fields"]:
        quality_report["recommendations"].append(
            f"Fix invalid fields: {', '.join(quality_report['invalid_fields'])}"
        )
    
    if quality_report["quality_score"] < 0.5:
        quality_report["recommendations"].append("Overall data quality is low - review all fields")
    
    return quality_report


def validate_client_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate client data and return validation result and errors."""
    errors = []
    
    # Check for required fields
    required_fields = ['client_name', 'email']
    for field in required_fields:
        if not any(field in key.lower() for key in data.keys()):
            errors.append(f"Missing required field: {field}")
    
    # Validate email if present
    email_fields = [key for key in data.keys() if 'email' in key.lower()]
    if email_fields:
        email_value = data[email_fields[0]]
        if not validate_email(str(email_value)):
            errors.append(f"Invalid email format: {email_value}")
    
    # Validate phone if present
    phone_fields = [key for key in data.keys() if 'phone' in key.lower()]
    if phone_fields:
        phone_value = data[phone_fields[0]]
        if not validate_phone(str(phone_value)):
            errors.append(f"Invalid phone format: {phone_value}")
    
    return len(errors) == 0, errors


def extract_structured_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract structured data from raw client data."""
    structured_data = {}
    
    # Field mappings for common variations
    field_mappings = {
        'client_name': ['name', 'client_name', 'full_name', 'clientName', 'fullName', 'customer_name'],
        'email': ['email', 'email_address', 'contact_email', 'emailAddress', 'contactEmail'],
        'phone': ['phone', 'phone_number', 'contact_phone', 'mobile', 'phoneNumber', 'contactPhone'],
        'project_type': ['project_type', 'projectType', 'type', 'service_type', 'serviceType'],
        'budget_range': ['budget', 'budget_range', 'budgetRange', 'price_range', 'priceRange'],
        'timeline': ['timeline', 'timeframe', 'deadline', 'completion_date', 'completionDate'],
        'address': ['address', 'location', 'property_address', 'propertyAddress', 'home_address'],
        'room_count': ['rooms', 'room_count', 'number_of_rooms', 'roomCount', 'numberOfRooms'],
        'square_feet': ['square_feet', 'squareFeet', 'area', 'size', 'property_size', 'propertySize'],
        'style_preference': ['style', 'style_preference', 'design_style', 'stylePreference', 'designStyle'],
        'urgency': ['urgency', 'priority', 'timeline_urgency', 'project_priority']
    }
    
    # Extract fields using mappings
    for standard_key, possible_keys in field_mappings.items():
        for key in possible_keys:
            if key in raw_data:
                value = raw_data[key]
                
                # Handle nested structures
                if isinstance(value, dict) and 'value' in value:
                    structured_data[standard_key] = value['value']
                elif isinstance(value, list) and len(value) > 0:
                    structured_data[standard_key] = value[0] if isinstance(value[0], str) else str(value[0])
                else:
                    structured_data[standard_key] = value
                break
    
    # Add any unmapped fields
    mapped_keys = set()
    for keys in field_mappings.values():
        mapped_keys.update(keys)
    
    unmapped_fields = {}
    for key, value in raw_data.items():
        if key not in mapped_keys:
            if isinstance(value, (str, int, float, bool)):
                unmapped_fields[key] = value
            elif isinstance(value, list):
                unmapped_fields[key] = str(value)
            elif isinstance(value, dict):
                unmapped_fields[key] = str(value)
    
    if unmapped_fields:
        structured_data['additional_fields'] = unmapped_fields
    
    return structured_data


def sanitize_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize data by removing sensitive information and normalizing values."""
    sanitized = {}
    
    # Fields that might contain sensitive information
    sensitive_fields = ['password', 'token', 'key', 'secret', 'auth', 'credential']
    
    for key, value in data.items():
        # Skip sensitive fields
        if any(sensitive in key.lower() for sensitive in sensitive_fields):
            continue
        
        # Sanitize string values
        if isinstance(value, str):
            # Remove excessive whitespace
            sanitized_value = ' '.join(value.split())
            # Truncate very long strings
            if len(sanitized_value) > 1000:
                sanitized_value = sanitized_value[:1000] + "..."
            sanitized[key] = sanitized_value
        else:
            sanitized[key] = value
    
    return sanitized


def validate_and_clean_data(data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """Validate and clean incoming data."""
    errors = []

    # Sanitize data first (preserves nested structure)
    cleaned_data = sanitize_data(data)

    # Validate data
    is_valid, validation_errors = validate_client_data(cleaned_data)
    errors.extend(validation_errors)

    # Assess quality
    quality_report = assess_data_quality(cleaned_data)
    if quality_report["quality_score"] < 0.3:
        errors.append("Data quality is very low - manual review recommended")

    return cleaned_data, errors
