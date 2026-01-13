# src/alerts/router.py
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from src.database import get_db
from src.auth.dependencies import get_current_user
from src.auth.models import User
from src.alerts import schemas, service
from src.alerts.constants import AlertStatus
from src.alerts.exceptions import AlertNotFoundException
from src.market_data import service as market_service

router = APIRouter()


# Update the create_alert function:
@router.post(
    "",
    response_model=schemas.AlertResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new price alert"
)
async def create_alert(
    alert_data: schemas.AlertCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new price alert with current price"""
    
    # Fetch current price from market data
    try:
        price_data = await market_service.get_current_price(
            alert_data.symbol,
            alert_data.asset_type
        )
        current_price = price_data.price
    except Exception as e:
        # If we can't get price, still create alert but without current_price
        current_price = None
    
    alert = await service.create_alert(
        db,
        current_user.id,
        alert_data,
        current_price
    )
    return alert


@router.get(
    "",
    response_model=schemas.AlertListResponse,
    summary="Get all alerts for current user"
)
async def get_my_alerts(
    status_filter: Optional[AlertStatus] = Query(None, description="Filter by alert status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all alerts for the authenticated user with pagination and filtering.
    
    - **status**: Optional filter by alert status (active, triggered, paused, deleted)
    - **page**: Page number (starts at 1)
    - **page_size**: Number of alerts per page (max 100)
    """
    skip = (page - 1) * page_size
    
    alerts = await service.get_user_alerts(
        db,
        current_user.id,
        status=status_filter,
        skip=skip,
        limit=page_size
    )
    
    total = await service.count_user_alerts(db, current_user.id, status=status_filter)
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "alerts": alerts
    }


@router.get(
    "/stats",
    response_model=schemas.AlertStatsResponse,
    summary="Get alert statistics"
)
async def get_alert_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get statistics about user's alerts.
    
    Returns counts of total, active, triggered, and paused alerts.
    """
    stats = await service.get_alert_stats(db, current_user.id)
    return stats


@router.get(
    "/{alert_id}",
    response_model=schemas.AlertResponse,
    summary="Get a specific alert"
)
async def get_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get details of a specific alert by ID.
    
    Only the owner of the alert can access it.
    """
    alert = await service.get_alert_by_id(db, alert_id)
    
    if not alert:
        raise AlertNotFoundException(alert_id)
    
    # Verify ownership
    await service.verify_alert_ownership(alert, current_user.id)
    
    return alert


@router.put(
    "/{alert_id}",
    response_model=schemas.AlertResponse,
    summary="Update an alert"
)
async def update_alert(
    alert_id: int,
    alert_data: schemas.AlertUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing alert.
    
    You can update:
    - target_price
    - percent_change
    - status (active, paused)
    - notification preferences
    
    Only the owner of the alert can update it.
    """
    alert = await service.get_alert_by_id(db, alert_id)
    
    if not alert:
        raise AlertNotFoundException(alert_id)
    
    # Verify ownership
    await service.verify_alert_ownership(alert, current_user.id)
    
    updated_alert = await service.update_alert(db, alert, alert_data)
    return updated_alert


@router.delete(
    "/{alert_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an alert"
)
async def delete_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an alert (soft delete - marks as deleted).
    
    Only the owner of the alert can delete it.
    """
    alert = await service.get_alert_by_id(db, alert_id)
    
    if not alert:
        raise AlertNotFoundException(alert_id)
    
    # Verify ownership
    await service.verify_alert_ownership(alert, current_user.id)
    
    await service.delete_alert(db, alert)
    return None