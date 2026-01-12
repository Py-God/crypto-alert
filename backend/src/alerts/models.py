# src/alerts/models.py
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.database import Base
from src.alerts.constants import AssetType, AlertType, AlertStatus


class Alert(Base):
    """Alert model for price notifications"""
    __tablename__ = "alerts"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Key to User
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Asset Information
    symbol = Column(String(20), nullable=False, index=True)
    asset_type = Column(SQLEnum(AssetType), nullable=False, index=True)
    
    # Alert Conditions
    alert_type = Column(SQLEnum(AlertType), nullable=False)
    target_price = Column(Float, nullable=False)
    percent_change = Column(Float, nullable=True)  # Only for PERCENT_CHANGE type
    
    # Alert Settings
    status = Column(SQLEnum(AlertStatus), default=AlertStatus.ACTIVE, nullable=False, index=True)
    notify_email = Column(Boolean, default=True, nullable=False)
    notify_sms = Column(Boolean, default=False, nullable=False)
    notify_websocket = Column(Boolean, default=True, nullable=False)
    
    # Tracking Information
    created_price = Column(Float, nullable=True)  # Price when alert was created
    triggered_price = Column(Float, nullable=True)  # Price when alert triggered
    triggered_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="alerts")
    
    def __repr__(self):
        return f"<Alert(id={self.id}, symbol={self.symbol}, type={self.alert_type}, target={self.target_price}, status={self.status})>"
    
    @property
    def is_active(self) -> bool:
        """Check if alert is active"""
        return self.status == AlertStatus.ACTIVE
    
    @property
    def is_triggered(self) -> bool:
        """Check if alert has been triggered"""
        return self.status == AlertStatus.TRIGGERED