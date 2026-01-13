# src/alerts/service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional, List
import structlog

from src.alerts.models import Alert
from src.alerts.schemas import AlertCreate, AlertUpdate
from src.alerts.constants import AlertStatus, MAX_ALERTS_PER_USER
from src.alerts.exceptions import (
    AlertNotFoundException,
    AlertLimitExceededException,
    UnauthorizedAlertAccessException
)

logger = structlog.get_logger()


async def get_alert_by_id(db: AsyncSession, alert_id: int) -> Optional[Alert]:
    """Get alert by ID (excluding deleted)"""
    query = select(Alert).where(
        and_(
            Alert.id == alert_id,
            Alert.status != AlertStatus.DELETED  # ← Exclude deleted
        )
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_user_alerts(
    db: AsyncSession,
    user_id: int,
    status: Optional[AlertStatus] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Alert]:
    """Get all alerts for a user (excluding deleted)"""
    query = select(Alert).where(
        and_(
            Alert.user_id == user_id,
            Alert.status != AlertStatus.DELETED  # ← Exclude deleted
        )
    )
    
    if status:
        query = query.where(Alert.status == status)
    
    # Order by created_at descending (newest first)
    query = query.order_by(Alert.created_at.desc())
    
    # Pagination
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


async def count_user_alerts(
    db: AsyncSession,
    user_id: int,
    status: Optional[AlertStatus] = None
) -> int:
    """Count alerts for a user (excluding deleted)"""
    query = select(func.count(Alert.id)).where(
        and_(
            Alert.user_id == user_id,
            Alert.status != AlertStatus.DELETED  # ← Exclude deleted
        )
    )
    
    if status:
        query = query.where(Alert.status == status)
    
    result = await db.execute(query)
    return result.scalar_one()


async def create_alert(
    db: AsyncSession,
    user_id: int,
    alert_data: AlertCreate,
    current_price: Optional[float] = None
) -> Alert:
    """Create a new alert"""
    
    # Check if user has reached alert limit (only count non-deleted)
    active_count = await count_user_alerts(
        db,
        user_id,
        status=AlertStatus.ACTIVE
    )
    
    if active_count >= MAX_ALERTS_PER_USER:
        raise AlertLimitExceededException(MAX_ALERTS_PER_USER)
    
    # Create alert
    alert = Alert(
        user_id=user_id,
        symbol=alert_data.symbol,
        asset_type=alert_data.asset_type,
        alert_type=alert_data.alert_type,
        target_price=alert_data.target_price,
        percent_change=alert_data.percent_change,
        notify_email=alert_data.notify_email,
        notify_sms=alert_data.notify_sms,
        notify_websocket=alert_data.notify_websocket,
        status=AlertStatus.ACTIVE,
        created_price=current_price
    )
    
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    
    logger.info(
        "alert_created",
        alert_id=alert.id,
        user_id=user_id,
        symbol=alert.symbol,
        alert_type=alert.alert_type.value
    )
    
    return alert


async def update_alert(
    db: AsyncSession,
    alert: Alert,
    alert_data: AlertUpdate
) -> Alert:
    """Update an existing alert"""
    
    # Update only provided fields
    update_data = alert_data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(alert, field, value)
    
    await db.commit()
    await db.refresh(alert)
    
    logger.info(
        "alert_updated",
        alert_id=alert.id,
        updated_fields=list(update_data.keys())
    )
    
    return alert


async def delete_alert(db: AsyncSession, alert: Alert) -> None:
    """Soft delete an alert (mark as deleted)"""
    alert.status = AlertStatus.DELETED
    await db.commit()
    
    logger.info("alert_deleted", alert_id=alert.id)


async def verify_alert_ownership(alert: Alert, user_id: int) -> None:
    """Verify that the alert belongs to the user"""
    if alert.user_id != user_id:
        raise UnauthorizedAlertAccessException()


async def get_alert_stats(db: AsyncSession, user_id: int) -> dict:
    """Get statistics about user's alerts (excluding deleted)"""
    
    # Count all non-deleted alerts
    total = await count_user_alerts(db, user_id)
    
    # Count by specific statuses
    active = await count_user_alerts(db, user_id, AlertStatus.ACTIVE)
    triggered = await count_user_alerts(db, user_id, AlertStatus.TRIGGERED)
    paused = await count_user_alerts(db, user_id, AlertStatus.PAUSED)
    
    return {
        "total_alerts": total,
        "active_alerts": active,
        "triggered_alerts": triggered,
        "paused_alerts": paused
    }


async def get_active_alerts_by_symbol(
    db: AsyncSession,
    symbol: str
) -> List[Alert]:
    """Get all active alerts for a specific symbol (used by monitoring service)"""
    query = select(Alert).where(
        and_(
            Alert.symbol == symbol.upper(),
            Alert.status == AlertStatus.ACTIVE
        )
    )
    result = await db.execute(query)
    return result.scalars().all()