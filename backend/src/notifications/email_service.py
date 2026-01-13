# src/notifications/email_service.py
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from jinja2 import Template
from typing import Optional
import structlog

from src.config import settings

logger = structlog.get_logger()


class EmailService:
    """Service for sending emails"""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL
        self.from_name = settings.SMTP_FROM_NAME
        self.use_tls = settings.SMTP_TLS
        
        # Check if email is configured
        self.is_configured = bool(
            self.smtp_user and 
            self.smtp_password and 
            self.from_email
        )
        
        if not self.is_configured:
            logger.warning("email_not_configured", message="Email credentials not set in .env")
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send an email
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text fallback (optional)
        
        Returns:
            True if sent successfully
        """
        if not self.is_configured:
            logger.warning("email_send_skipped", reason="Email not configured")
            return False
        
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email
            
            # Add plain text version
            if text_content:
                part1 = MIMEText(text_content, "plain")
                message.attach(part1)
            
            # Add HTML version
            part2 = MIMEText(html_content, "html")
            message.attach(part2)
            
            # Send email
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                use_tls=self.use_tls,
            )
            
            logger.info("email_sent", to=to_email, subject=subject)
            return True
            
        except Exception as e:
            logger.error("email_send_failed", to=to_email, error=str(e))
            return False
    
    def render_template(self, template_name: str, context: dict) -> str:
        """
        Render an email template
        
        Args:
            template_name: Name of template file (e.g., "alert_triggered.html")
            context: Template variables
        
        Returns:
            Rendered HTML string
        """
        template_path = Path(__file__).parent / "templates" / template_name
        
        if not template_path.exists():
            logger.error("template_not_found", template=template_name)
            return f"<html><body><h1>Alert Notification</h1><p>{context.get('message', 'Alert triggered')}</p></body></html>"
        
        template_content = template_path.read_text()
        template = Template(template_content)
        
        return template.render(**context)
    
    async def send_alert_email(
        self,
        to_email: str,
        user_name: str,
        symbol: str,
        asset_type: str,
        alert_type: str,
        current_price: float,
        target_price: float,
        message: str,
        triggered_at: str
    ) -> bool:
        """
        Send alert triggered email
        
        Args:
            to_email: User's email
            user_name: User's name
            symbol: Asset symbol
            asset_type: "stock" or "crypto"
            alert_type: "above", "below", or "percent_change"
            current_price: Current price
            target_price: Target price
            message: Alert message
            triggered_at: Timestamp
        
        Returns:
            True if sent successfully
        """
        # Render template
        html_content = self.render_template("alert_triggered.html", {
            "user_name": user_name,
            "symbol": symbol,
            "asset_type": asset_type,
            "alert_type": alert_type,
            "current_price": current_price,
            "target_price": target_price,
            "message": message,
            "triggered_at": triggered_at,
            "app_url": "http://localhost:8000",  # TODO: Make configurable
        })
        
        # Plain text fallback
        text_content = f"""
        Price Alert Triggered!
        
        {symbol} ({asset_type.upper()})
        Current Price: ${current_price:,.2f}
        Your Target: ${target_price:,.2f}
        Alert Type: {alert_type.upper()}
        
        {message}
        
        Triggered at: {triggered_at}
        
        View your alerts: http://localhost:8000/alerts
        """
        
        subject = f"🔔 {symbol} Alert Triggered - ${current_price:,.2f}"
        
        return await self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )


# Global email service instance
email_service = EmailService()