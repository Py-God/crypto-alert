# src/alerts/constants.py
from enum import Enum


class AssetType(str, Enum):
    """Types of assets that can be monitored"""
    STOCK = "stock"
    CRYPTO = "crypto"


class AlertType(str, Enum):
    """Types of price alerts"""
    ABOVE = "above"           # Alert when price goes above target
    BELOW = "below"           # Alert when price goes below target
    PERCENT_CHANGE = "percent_change"  # Alert when price changes by X%


class AlertStatus(str, Enum):
    """Status of an alert"""
    ACTIVE = "active"         # Alert is active and monitoring
    TRIGGERED = "triggered"   # Alert has been triggered
    PAUSED = "paused"        # Alert is paused by user
    DELETED = "deleted"      # Alert is soft-deleted


# Alert limits
MAX_ALERTS_PER_USER = 100
MIN_TARGET_PRICE = 0.01
MAX_TARGET_PRICE = 1000000000
MIN_PERCENT_CHANGE = 0.1
MAX_PERCENT_CHANGE = 100.0