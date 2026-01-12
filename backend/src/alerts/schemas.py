# src/alerts/schemas.py
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional

from src.alerts.constants import (
    AssetType,
    AlertType,
    AlertStatus,
    MIN_TARGET_PRICE,
    MAX_TARGET_PRICE,
    MIN_PERCENT_CHANGE,
    MAX_PERCENT_CHANGE
)


class AlertBase(BaseModel):
    """Base schema for alerts"""
    symbol: str = Field(..., min_length=1, max_length=20, description="Stock/Crypto symbol (e.g., BTC, AAPL)")
    asset_type: AssetType = Field(..., description="Type of asset: stock or crypto")
    alert_type: AlertType = Field(..., description="Type of alert: above, below, or percent_change")
    target_price: float = Field(..., gt=MIN_TARGET_PRICE, lt=MAX_TARGET_PRICE, description="Target price for alert")
    percent_change: Optional[float] = Field(None, description="Percent change threshold (only for PERCENT_CHANGE alerts)")
    notify_email: bool = Field(True, description="Send email notification when triggered")
    notify_sms: bool = Field(False, description="Send SMS notification when triggered")
    notify_websocket: bool = Field(True, description="Send WebSocket notification when triggered")
    
    @validator('symbol')
    def symbol_uppercase(cls, v):
        """Convert symbol to uppercase"""
        return v.upper().strip()
    
    @validator('percent_change')
    def validate_percent_change(cls, v, values):
        """Validate percent_change is only set for PERCENT_CHANGE alerts"""
        alert_type = values.get('alert_type')
        
        if alert_type == AlertType.PERCENT_CHANGE:
            if v is None:
                raise ValueError('percent_change is required for PERCENT_CHANGE alert type')
            if v < MIN_PERCENT_CHANGE or v > MAX_PERCENT_CHANGE:
                raise ValueError(f'percent_change must be between {MIN_PERCENT_CHANGE} and {MAX_PERCENT_CHANGE}')
        else:
            if v is not None:
                raise ValueError('percent_change should only be set for PERCENT_CHANGE alert type')
        
        return v


class AlertCreate(AlertBase):
    """Schema for creating an alert"""
    pass


class AlertUpdate(BaseModel):
    """Schema for updating an alert"""
    target_price: Optional[float] = Field(None, gt=MIN_TARGET_PRICE, lt=MAX_TARGET_PRICE)
    percent_change: Optional[float] = Field(None, ge=MIN_PERCENT_CHANGE, le=MAX_PERCENT_CHANGE)
    status: Optional[AlertStatus] = None
    notify_email: Optional[bool] = None
    notify_sms: Optional[bool] = None
    notify_websocket: Optional[bool] = None


class AlertResponse(AlertBase):
    """Schema for alert responses"""
    id: int
    user_id: int
    status: AlertStatus
    created_price: Optional[float]
    triggered_price: Optional[float]
    triggered_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class AlertListResponse(BaseModel):
    """Schema for paginated alert list"""
    total: int
    page: int
    page_size: int
    alerts: list[AlertResponse]


class AlertStatsResponse(BaseModel):
    """Schema for user's alert statistics"""
    total_alerts: int
    active_alerts: int
    triggered_alerts: int
    paused_alerts: int