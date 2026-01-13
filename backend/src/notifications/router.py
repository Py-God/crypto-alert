# src/notifications/router.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr

from src.auth.dependencies import get_current_user
from src.auth.models import User
from src.notifications.email_service import email_service

router = APIRouter()


class TestEmailRequest(BaseModel):
    """Request to send test email"""
    to_email: EmailStr


@router.post("/test-email")
async def send_test_email(
    request: TestEmailRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Send a test email to verify email configuration
    
    Requires authentication.
    """
    if not email_service.is_configured:
        raise HTTPException(
            status_code=503,
            detail="Email service is not configured. Please set SMTP credentials in .env"
        )
    
    success = await email_service.send_alert_email(
        to_email=request.to_email,
        user_name=current_user.username,
        symbol="BTC",
        asset_type="crypto",
        alert_type="above",
        current_price=42350.75,
        target_price=40000.00,
        message="🚀 BTC reached $42,350.75, above your target of $40,000.00 (This is a test email)",
        triggered_at="2026-01-09T22:30:00Z"
    )
    
    if success:
        return {
            "message": f"Test email sent successfully to {request.to_email}",
            "success": True
        }
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to send test email. Check server logs for details."
        )