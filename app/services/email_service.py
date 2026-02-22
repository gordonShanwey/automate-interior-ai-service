"""Email service for the Interior AI Service."""

import smtplib
import uuid
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional, List

from app.config import get_settings
from app.models.client_profile import ClientProfile
from app.models.email_models import EmailReport, EmailStatus, EmailTemplate, EmailConfiguration
from app.utils.errors import EmailServiceError, handle_service_error
from app.utils.logging import log_email_operation, timed_operation, StructuredLogger

logger = StructuredLogger("email_service")


class EmailService:
    """Email service for sending client profile reports."""
    
    def __init__(self):
        self.settings = get_settings()
        self.config = self._create_email_config()
        self.templates = self._load_default_templates()
        
        logger.info(
            f"📧 Email Service initialized",
            smtp_server=self.config.smtp_server,
            sender_email=self.config.sender_email
        )
    
    def _create_email_config(self) -> EmailConfiguration:
        """Create email configuration from settings."""
        return EmailConfiguration(
            smtp_server=self.settings.smtp_server,
            smtp_port=self.settings.smtp_port,
            smtp_username=self.settings.smtp_username,
            smtp_password=self.settings.smtp_password,
            smtp_use_tls=self.settings.smtp_use_tls,
            smtp_use_ssl=False,
            sender_email=self.settings.smtp_username,
            sender_name="Interior AI Service",
            default_recipients=[self.settings.designer_email],
            max_retry_attempts=self.settings.max_retry_attempts,
            retry_delay_seconds=self.settings.retry_delay_seconds
        )
    
    def _load_default_templates(self) -> Dict[str, EmailTemplate]:
        """Load default email templates."""
        templates = {}
        
        # Client profile report template
        client_profile_template = EmailTemplate(
            name="client_profile_report",
            subject="Nowy profil klienta: {client_name}",
            html_template="""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Profil klienta: {client_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }}
        .section {{ margin-bottom: 30px; padding: 20px; background: #f9f9f9; border-radius: 8px; }}
        .section h2 {{ color: #667eea; margin-top: 0; }}
        .recommendation {{ background: white; padding: 15px; margin: 10px 0; border-left: 4px solid #667eea; border-radius: 4px; }}
        .priority-high {{ border-left-color: #e74c3c; }}
        .priority-medium {{ border-left-color: #f39c12; }}
        .priority-low {{ border-left-color: #27ae60; }}
        .next-steps {{ background: #e8f4fd; padding: 15px; border-radius: 8px; }}
        .next-steps ol {{ margin: 0; padding-left: 20px; }}
        .footer {{ text-align: center; margin-top: 40px; padding: 20px; background: #f5f5f5; border-radius: 8px; font-size: 14px; color: #666; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; background: white; border-radius: 5px; text-align: center; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #667eea; }}
        .metric-label {{ font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎨 Profil klienta: {client_name}</h1>
        <p>Wygenerowano: {generated_date}</p>
    </div>

    <div class="section">
        <h2>📋 Przegląd projektu</h2>
        <p><strong>Typ:</strong> {project_type}</p>
        <p><strong>Podsumowanie:</strong> {project_summary}</p>

        <div style="display: flex; justify-content: space-around; margin: 20px 0;">
            <div class="metric">
                <div class="metric-value">{recommendations_count}</div>
                <div class="metric-label">Zalecenia</div>
            </div>
            <div class="metric">
                <div class="metric-value">{budget_range}</div>
                <div class="metric-label">Budżet</div>
            </div>
            <div class="metric">
                <div class="metric-value">{timeline}</div>
                <div class="metric-label">Harmonogram</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>🏠 Szczegóły nieruchomości</h2>
        <p><strong>Adres:</strong> {property_address}</p>
        <p><strong>Pokoje:</strong> {room_count}</p>
        <p><strong>Powierzchnia:</strong> {square_feet}</p>
    </div>

    <div class="section">
        <h2>🎯 Preferencje klienta</h2>
        <p><strong>Styl:</strong> {style_preference}</p>
        <p><strong>Pilność:</strong> {urgency}</p>
    </div>

    <div class="section">
        <h2>🤖 Analiza AI</h2>
        <h3>Analiza stylu projektowego</h3>
        <p>{design_style_analysis}</p>

        <h3>Analiza przestrzeni</h3>
        <p>{space_analysis}</p>

        <h3>Uwagi budżetowe</h3>
        <p>{budget_analysis}</p>

        <h3>Analiza harmonogramu</h3>
        <p>{timeline_analysis}</p>
    </div>

    <div class="section">
        <h2>💡 Zalecenia projektowe</h2>
        {recommendations_html}
    </div>

    <div class="section">
        <h2>📝 Ogólne zalecenie</h2>
        <p>{overall_recommendation}</p>
    </div>

    <div class="section next-steps">
        <h2>🚀 Kolejne kroki</h2>
        <ol>
            {next_steps_html}
        </ol>
    </div>

    <div class="section">
        <h2>💰 Szacunki projektu</h2>
        <p><strong>Czas trwania:</strong> {estimated_duration}</p>
        <p><strong>Całkowity koszt:</strong> {estimated_cost}</p>
    </div>

    <div class="footer">
        <p>Wygenerowano przez Interior AI Service za pomocą {ai_model}</p>
        <p>Wskaźnik pewności: {confidence_score}</p>
    </div>
</body>
</html>
            """,
            text_template="""
PROFIL KLIENTA: {client_name}
Wygenerowano: {generated_date}

PRZEGLĄD PROJEKTU
Typ: {project_type}
Podsumowanie: {project_summary}

SZCZEGÓŁY NIERUCHOMOŚCI
Adres: {property_address}
Pokoje: {room_count}
Powierzchnia: {square_feet}

PREFERENCJE KLIENTA
Styl: {style_preference}
Pilność: {urgency}

ANALIZA AI
Styl projektowy: {design_style_analysis}
Analiza przestrzeni: {space_analysis}
Uwagi budżetowe: {budget_analysis}
Analiza harmonogramu: {timeline_analysis}

ZALECENIA PROJEKTOWE
{recommendations_text}

OGÓLNE ZALECENIE
{overall_recommendation}

KOLEJNE KROKI
{next_steps_text}

SZACUNKI PROJEKTU
Czas trwania: {estimated_duration}
Całkowity koszt: {estimated_cost}

Wygenerowano przez Interior AI Service za pomocą {ai_model}
Wskaźnik pewności: {confidence_score}
            """,
            variables=[
                "client_name", "generated_date", "project_type", "project_summary",
                "recommendations_count", "budget_range", "timeline", "property_address",
                "room_count", "square_feet", "style_preference", "urgency",
                "design_style_analysis", "space_analysis", "budget_analysis",
                "timeline_analysis", "recommendations_html", "overall_recommendation",
                "next_steps_html", "estimated_duration", "estimated_cost",
                "ai_model", "confidence_score", "recommendations_text", "next_steps_text"
            ]
        )
        
        templates["client_profile_report"] = client_profile_template
        return templates
    
    def send_profile_report(self, profile: ClientProfile, 
                           recipient_email: Optional[str] = None) -> EmailStatus:
        """Send client profile report via email."""
        with timed_operation("send_profile_report", client_name=profile.client_name):
            try:
                # Determine recipient
                recipient = recipient_email or self.config.default_recipients[0]
                
                # Create email report
                email_report = self._create_profile_email(profile, recipient)
                
                # Send email
                message_id = self._send_email(email_report)
                
                # Create status tracking
                status = EmailStatus(
                    message_id=message_id,
                    status="sent",
                    recipient_email=recipient,
                    sent_at=datetime.utcnow(),
                    subject=email_report.subject,
                    template_used="client_profile_report"
                )
                
                log_email_operation(
                    recipient=recipient,
                    template="client_profile_report",
                    status="sent",
                    message_id=message_id,
                    client_name=profile.client_name
                )
                
                return status
                
            except Exception as e:
                handle_service_error(
                    e, "Email", "send_profile_report",
                    client_name=profile.client_name,
                    recipient=recipient_email
                )
    
    def _create_profile_email(self, profile: ClientProfile, recipient: str) -> EmailReport:
        """Create email report from client profile."""
        template = self.templates["client_profile_report"]
        
        # Prepare template variables
        variables = {
            "client_name": profile.client_name,
            "generated_date": profile.generated_at.strftime("%d.%m.%Y, %H:%M UTC"),
            "project_type": profile.project_type,
            "project_summary": profile.project_summary,
            "recommendations_count": len(profile.recommendations),
            "budget_range": profile.budget_range or "Nie podano",
            "timeline": profile.timeline or "Nie podano",
            "property_address": profile.property_address or "Nie podano",
            "room_count": profile.room_count or "Nie podano",
            "square_feet": profile.square_feet or "Nie podano",
            "style_preference": profile.style_preference or "Nie podano",
            "urgency": profile.urgency or "Nie podano",
            "design_style_analysis": profile.design_style_analysis,
            "space_analysis": profile.space_analysis,
            "budget_analysis": profile.budget_analysis,
            "timeline_analysis": profile.timeline_analysis,
            "overall_recommendation": profile.overall_recommendation,
            "estimated_duration": profile.estimated_project_duration or "Nie podano",
            "estimated_cost": profile.estimated_total_cost or "Nie podano",
            "ai_model": profile.ai_model_used,
            "confidence_score": f"{profile.confidence_score:.2f}" if profile.confidence_score else "Niedostępny"
        }
        
        # Generate recommendations HTML
        recommendations_html = ""
        recommendations_text = ""
        for i, rec in enumerate(profile.recommendations, 1):
            priority_class = f"priority-{rec.priority}"
            recommendations_html += f"""
            <div class="recommendation {priority_class}">
                <h3>{i}. {rec.title}</h3>
                <p><strong>Kategoria:</strong> {rec.category}</p>
                <p><strong>Priorytet:</strong> {rec.priority.title()}</p>
                <p><strong>Opis:</strong> {rec.description}</p>
                <p><strong>Uzasadnienie:</strong> {rec.reasoning}</p>
                <p><strong>Szacowany koszt:</strong> {rec.estimated_cost or 'Nie podano'}</p>
                <p><strong>Harmonogram:</strong> {rec.timeline or 'Nie podano'}</p>
            </div>
            """

            recommendations_text += f"""
{i}. {rec.title} ({rec.category})
   Priorytet: {rec.priority.title()}
   Opis: {rec.description}
   Uzasadnienie: {rec.reasoning}
   Szacowany koszt: {rec.estimated_cost or 'Nie podano'}
   Harmonogram: {rec.timeline or 'Nie podano'}

"""
        
        variables["recommendations_html"] = recommendations_html
        variables["recommendations_text"] = recommendations_text
        
        # Generate next steps HTML
        next_steps_html = ""
        next_steps_text = ""
        for step in profile.next_steps:
            next_steps_html += f"<li>{step}</li>"
            next_steps_text += f"• {step}\n"
        
        variables["next_steps_html"] = next_steps_html
        variables["next_steps_text"] = next_steps_text
        
        # Format templates
        subject = template.subject.format(**variables)
        html_content = template.html_template.format(**variables)
        text_content = template.text_template.format(**variables)
        
        return EmailReport(
            subject=subject,
            recipient_email=recipient,
            html_content=html_content,
            text_content=text_content,
            template_used="client_profile_report",
            variables_used=variables
        )
    
    def _send_email(self, email_report: EmailReport) -> str:
        """Send email using SMTP."""
        message_id = str(uuid.uuid4())
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = email_report.subject
        msg['From'] = f"{self.config.sender_name} <{self.config.sender_email}>"
        msg['To'] = email_report.recipient_email
        msg['Message-ID'] = f"<{message_id}@{self.config.smtp_server}>"
        
        # Attach content
        text_part = MIMEText(email_report.text_content, 'plain', 'utf-8')
        html_part = MIMEText(email_report.html_content, 'html', 'utf-8')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Send email
        try:
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                if self.config.smtp_use_tls:
                    server.starttls()
                
                server.login(self.config.smtp_username, self.config.smtp_password)
                server.send_message(msg)
                
                logger.info(
                    f"✅ Email sent successfully",
                    message_id=message_id,
                    recipient=email_report.recipient_email,
                    subject=email_report.subject
                )
                
                return message_id
                
        except smtplib.SMTPAuthenticationError as e:
            raise EmailServiceError(
                f"SMTP authentication failed: {str(e)}",
                recipient=email_report.recipient_email,
                smtp_error=str(e)
            )
        except smtplib.SMTPRecipientsRefused as e:
            raise EmailServiceError(
                f"Recipient refused: {str(e)}",
                recipient=email_report.recipient_email,
                smtp_error=str(e)
            )
        except smtplib.SMTPServerDisconnected as e:
            raise EmailServiceError(
                f"SMTP server disconnected: {str(e)}",
                recipient=email_report.recipient_email,
                smtp_error=str(e)
            )
        except Exception as e:
            raise EmailServiceError(
                f"Failed to send email: {str(e)}",
                recipient=email_report.recipient_email,
                smtp_error=str(e)
            )
    
    def test_connection(self) -> Dict[str, Any]:
        """Test email service connection."""
        try:
            with timed_operation("test_email_connection"):
                # Test SMTP connection
                with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                    if self.config.smtp_use_tls:
                        server.starttls()
                    
                    server.login(self.config.smtp_username, self.config.smtp_password)
                    
                    return {
                        "status": "connected",
                        "smtp_server": self.config.smtp_server,
                        "sender_email": self.config.sender_email,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
        except Exception as e:
            return {
                "status": "error",
                "smtp_server": self.config.smtp_server,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Global service instance
_email_service_instance = None


def get_email_service() -> EmailService:
    """Get the global email service instance."""
    global _email_service_instance
    if _email_service_instance is None:
        _email_service_instance = EmailService()
    return _email_service_instance
