"""Email models for the Interior AI Service."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr


class EmailTemplate(BaseModel):
    """Email template configuration."""
    
    name: str = Field(..., description="Template name")
    subject: str = Field(..., description="Email subject line")
    html_template: str = Field(..., description="HTML email template")
    text_template: str = Field(..., description="Plain text email template")
    variables: List[str] = Field(default=[], description="Template variables")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "client_profile_report",
                "subject": "New Client Profile: {client_name}",
                "html_template": "<h1>Client Profile: {client_name}</h1>...",
                "text_template": "Client Profile: {client_name}\n...",
                "variables": ["client_name", "project_type", "recommendations_count"]
            }
        }


class EmailReport(BaseModel):
    """Email report content structure."""
    
    subject: str = Field(..., description="Email subject")
    recipient_email: EmailStr = Field(..., description="Recipient email address")
    recipient_name: Optional[str] = Field(None, description="Recipient name")
    
    # Content
    html_content: str = Field(..., description="HTML email content")
    text_content: str = Field(..., description="Plain text email content")
    
    # Metadata
    template_used: Optional[str] = Field(None, description="Email template used")
    variables_used: Dict[str, Any] = Field(default={}, description="Template variables")
    
    # Tracking
    message_id: Optional[str] = Field(None, description="Email message ID")
    sent_at: Optional[datetime] = Field(None, description="When email was sent")
    
    class Config:
        json_schema_extra = {
            "example": {
                "subject": "New Client Profile: Sarah Johnson",
                "recipient_email": "designer@interiorstudio.com",
                "html_content": "<h1>Client Profile: Sarah Johnson</h1>...",
                "text_content": "Client Profile: Sarah Johnson\n...",
                "template_used": "client_profile_report",
                "variables_used": {"client_name": "Sarah Johnson", "project_type": "Living Room Redesign"}
            }
        }


class EmailStatus(BaseModel):
    """Email delivery status tracking."""
    
    message_id: str = Field(..., description="Email message ID")
    status: str = Field(..., description="Delivery status (sent, delivered, failed, pending)")
    recipient_email: EmailStr = Field(..., description="Recipient email address")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When email was created")
    sent_at: Optional[datetime] = Field(None, description="When email was sent")
    delivered_at: Optional[datetime] = Field(None, description="When email was delivered")
    
    # Error information
    error_message: Optional[str] = Field(None, description="Error message if delivery failed")
    retry_count: int = Field(default=0, description="Number of retry attempts")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    
    # Metadata
    subject: str = Field(..., description="Email subject")
    template_used: Optional[str] = Field(None, description="Template used")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message_id": "msg_123456789",
                "status": "delivered",
                "recipient_email": "designer@interiorstudio.com",
                "subject": "New Client Profile: Sarah Johnson",
                "sent_at": "2024-01-15T10:30:00Z",
                "delivered_at": "2024-01-15T10:30:05Z"
            }
        }
    
    def is_final_status(self) -> bool:
        """Check if this is a final status (delivered or failed permanently)."""
        return self.status in ["delivered", "failed"] and self.retry_count >= self.max_retries
    
    def can_retry(self) -> bool:
        """Check if email can be retried."""
        return self.status == "failed" and self.retry_count < self.max_retries
    
    def mark_sent(self) -> None:
        """Mark email as sent."""
        self.status = "sent"
        self.sent_at = datetime.utcnow()
    
    def mark_delivered(self) -> None:
        """Mark email as delivered."""
        self.status = "delivered"
        self.delivered_at = datetime.utcnow()
    
    def mark_failed(self, error_message: str) -> None:
        """Mark email as failed."""
        self.status = "failed"
        self.error_message = error_message
        self.retry_count += 1


class EmailConfiguration(BaseModel):
    """Email service configuration."""
    
    smtp_server: str = Field(..., description="SMTP server hostname")
    smtp_port: int = Field(..., description="SMTP server port")
    smtp_username: str = Field(..., description="SMTP username")
    smtp_password: str = Field(..., description="SMTP password")
    smtp_use_tls: bool = Field(default=True, description="Use TLS encryption")
    smtp_use_ssl: bool = Field(default=False, description="Use SSL encryption")
    
    # Sender information
    sender_email: str = Field(..., description="Sender email address")
    sender_name: str = Field(..., description="Sender display name")
    
    # Default recipients
    default_recipients: List[EmailStr] = Field(default=[], description="Default recipient emails")
    
    # Retry configuration
    max_retry_attempts: int = Field(default=3, description="Maximum retry attempts")
    retry_delay_seconds: int = Field(default=60, description="Delay between retries")
    
    # Templates
    templates: Dict[str, EmailTemplate] = Field(default={}, description="Available email templates")
    
    class Config:
        json_schema_extra = {
            "example": {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "smtp_username": "service@interiorstudio.com",
                "sender_email": "service@interiorstudio.com",
                "sender_name": "Interior AI Service",
                "default_recipients": ["designer@interiorstudio.com"]
            }
        }
    
    def get_template(self, template_name: str) -> Optional[EmailTemplate]:
        """Get email template by name."""
        return self.templates.get(template_name)
    
    def add_template(self, template: EmailTemplate) -> None:
        """Add or update email template."""
        self.templates[template.name] = template
    
    def validate_configuration(self) -> bool:
        """Validate email configuration."""
        required_fields = [
            self.smtp_server, self.smtp_username, self.smtp_password,
            self.sender_email, self.sender_name
        ]
        return all(field for field in required_fields) and self.smtp_port > 0
