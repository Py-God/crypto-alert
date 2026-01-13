# src/monitoring/alert_checker.py
from typing import List
from datetime import datetime
import structlog

from src.alerts.models import Alert, AlertType, AlertStatus
from src.websocket.manager import manager

logger = structlog.get_logger()


class AlertChecker:
    """Check if alerts should be triggered based on current price"""
    
    @staticmethod
    def should_trigger_alert(alert: Alert, current_price: float) -> bool:
        """
        Check if an alert should be triggered
        
        Args:
            alert: Alert object
            current_price: Current price of the asset
        
        Returns:
            True if alert should be triggered
        """
        if alert.status != AlertStatus.ACTIVE:
            return False
        
        if alert.alert_type == AlertType.ABOVE:
            return current_price >= alert.target_price
        
        elif alert.alert_type == AlertType.BELOW:
            return current_price <= alert.target_price
        
        elif alert.alert_type == AlertType.PERCENT_CHANGE:
            if alert.created_price is None:
                return False
            
            percent_change = abs(
                ((current_price - alert.created_price) / alert.created_price) * 100
            )
            return percent_change >= alert.percent_change
        
        return False
    
    @staticmethod
    def generate_trigger_message(alert: Alert, current_price: float) -> str:
        """Generate human-readable trigger message"""
        
        if alert.alert_type == AlertType.ABOVE:
            return (
                f"🚀 {alert.symbol} reached ${current_price:,.2f}, "
                f"above your target of ${alert.target_price:,.2f}"
            )
        
        elif alert.alert_type == AlertType.BELOW:
            return (
                f"📉 {alert.symbol} dropped to ${current_price:,.2f}, "
                f"below your target of ${alert.target_price:,.2f}"
            )
        
        elif alert.alert_type == AlertType.PERCENT_CHANGE:
            if alert.created_price:
                change = ((current_price - alert.created_price) / alert.created_price) * 100
                direction = "up" if change > 0 else "down"
                return (
                    f"📊 {alert.symbol} changed {abs(change):.2f}% {direction} "
                    f"from ${alert.created_price:,.2f} to ${current_price:,.2f}"
                )
        
        return f"Alert triggered for {alert.symbol} at ${current_price:,.2f}"
    
    @staticmethod
    async def notify_user(
        alert: Alert,
        current_price: float,
        message: str
    ):
        """Send notifications to user through various channels"""
        
        # WebSocket notification
        if alert.notify_websocket:
            await manager.send_alert_notification(
                user_id=alert.user_id,
                alert_id=alert.id,
                symbol=alert.symbol,
                current_price=current_price,
                target_price=alert.target_price,
                alert_type=alert.alert_type.value
            )
        
        # Email notification (to be implemented later)
        if alert.notify_email:
            logger.info("email_notification_queued", alert_id=alert.id)
            # TODO: Implement email sending
        
        # SMS notification (to be implemented later)
        if alert.notify_sms:
            logger.info("sms_notification_queued", alert_id=alert.id)
            # TODO: Implement SMS sending