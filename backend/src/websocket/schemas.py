# src/websocket/schemas.py
from pydantic import BaseModel
from typing import Optional, List


class WebSocketMessage(BaseModel):
    """Base WebSocket message"""
    type: str
    data: Optional[dict] = None


class SubscribeMessage(BaseModel):
    """Subscribe to symbol updates"""
    type: str = "subscribe"
    symbol: str


class UnsubscribeMessage(BaseModel):
    """Unsubscribe from symbol updates"""
    type: str = "unsubscribe"
    symbol: str


class PingMessage(BaseModel):
    """Ping message for keepalive"""
    type: str = "ping"


class ConnectionStats(BaseModel):
    """WebSocket connection statistics"""
    active_users: int
    total_connections: int
    watched_symbols: int
    symbols: List[str]