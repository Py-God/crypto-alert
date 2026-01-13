# src/market_data/schemas.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PriceData(BaseModel):
    """Schema for price data"""
    symbol: str
    asset_type: str
    price: float = Field(..., gt=0)
    timestamp: datetime
    source: str  # "binance", "yahoo", "coingecko"
    
    class Config:
        from_attributes = True


class PriceHistory(BaseModel):
    """Schema for historical price data"""
    symbol: str
    asset_type: str
    prices: list[dict]  # [{timestamp, price, volume}, ...]
    interval: str  # "1m", "5m", "1h", "1d"
    source: str


class SymbolInfo(BaseModel):
    """Schema for symbol information"""
    symbol: str
    asset_type: str
    name: Optional[str] = None
    exchange: Optional[str] = None
    available: bool = True


class MultiplePricesRequest(BaseModel):
    """Schema for requesting multiple prices"""
    symbols: list[str] = Field(..., min_length=1, max_length=50)
    asset_type: str


class MultiplePricesResponse(BaseModel):
    """Schema for multiple price responses"""
    prices: dict[str, PriceData]
    errors: dict[str, str] = {}