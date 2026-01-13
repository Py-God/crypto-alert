# src/websocket/manager.py
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set
import structlog
import json
from datetime import datetime

logger = structlog.get_logger()


class ConnectionManager:
    """WebSocket connection manager for real-time alerts and price updates"""
    
    def __init__(self):
        # user_id -> List[WebSocket]
        self.active_connections: Dict[int, List[WebSocket]] = {}
        
        # symbol -> Set[user_id] (users watching this symbol)
        self.symbol_watchers: Dict[str, Set[int]] = {}
        
        # WebSocket -> user_id (reverse lookup)
        self.websocket_users: Dict[WebSocket, int] = {}
        
    async def connect(self, websocket: WebSocket, user_id: int):
        """Connect a new WebSocket for a user"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        
        self.active_connections[user_id].append(websocket)
        self.websocket_users[websocket] = user_id
        
        logger.info(
            "websocket_connected",
            user_id=user_id,
            total_connections=len(self.active_connections[user_id])
        )
        
        # Send welcome message
        await self.send_personal_message({
            "type": "connected",
            "message": "Connected to Stock/Crypto Alert System",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }, user_id)
        
    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket"""
        user_id = self.websocket_users.get(websocket)
        
        if not user_id:
            return
        
        # Remove from active connections
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            
            # Clean up if no more connections
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                
                # Remove from all symbol watchers
                for symbol in list(self.symbol_watchers.keys()):
                    if user_id in self.symbol_watchers[symbol]:
                        self.symbol_watchers[symbol].remove(user_id)
                    if not self.symbol_watchers[symbol]:
                        del self.symbol_watchers[symbol]
        
        # Remove from websocket_users
        if websocket in self.websocket_users:
            del self.websocket_users[websocket]
        
        logger.info("websocket_disconnected", user_id=user_id)
    
    def subscribe_to_symbol(self, user_id: int, symbol: str):
        """Subscribe user to symbol price updates"""
        symbol = symbol.upper()
        
        if symbol not in self.symbol_watchers:
            self.symbol_watchers[symbol] = set()
        
        self.symbol_watchers[symbol].add(user_id)
        
        logger.info("user_subscribed_to_symbol", user_id=user_id, symbol=symbol)
    
    def unsubscribe_from_symbol(self, user_id: int, symbol: str):
        """Unsubscribe user from symbol"""
        symbol = symbol.upper()
        
        if symbol in self.symbol_watchers:
            self.symbol_watchers[symbol].discard(user_id)
            
            if not self.symbol_watchers[symbol]:
                del self.symbol_watchers[symbol]
        
        logger.info("user_unsubscribed_from_symbol", user_id=user_id, symbol=symbol)
    
    def get_user_subscriptions(self, user_id: int) -> List[str]:
        """Get all symbols a user is subscribed to"""
        subscriptions = []
        for symbol, users in self.symbol_watchers.items():
            if user_id in users:
                subscriptions.append(symbol)
        return subscriptions
    
    async def send_personal_message(self, message: dict, user_id: int):
        """Send message to specific user (all their connections)"""
        if user_id not in self.active_connections:
            return
        
        dead_connections = []
        
        for connection in self.active_connections[user_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error("send_message_failed", user_id=user_id, error=str(e))
                dead_connections.append(connection)
        
        # Clean up dead connections
        for conn in dead_connections:
            self.disconnect(conn)
    
    async def broadcast_to_symbol_watchers(self, symbol: str, message: dict):
        """Broadcast message to all users watching this symbol"""
        symbol = symbol.upper()
        
        if symbol not in self.symbol_watchers:
            return
        
        for user_id in list(self.symbol_watchers[symbol]):
            await self.send_personal_message(message, user_id)
    
    async def send_price_update(self, symbol: str, price: float, asset_type: str):
        """Send price update to all watchers of a symbol"""
        message = {
            "type": "price_update",
            "data": {
                "symbol": symbol,
                "price": price,
                "asset_type": asset_type,
                "timestamp": datetime.utcnow().isoformat(),
            }
        }
        await self.broadcast_to_symbol_watchers(symbol, message)
        
        logger.info("price_update_broadcast", symbol=symbol, price=price, watchers=len(self.symbol_watchers.get(symbol.upper(), [])))
    
    async def send_alert_notification(
        self,
        user_id: int,
        alert_id: int,
        symbol: str,
        current_price: float,
        target_price: float,
        alert_type: str
    ):
        """Send alert notification to user"""
        message = {
            "type": "alert_triggered",
            "data": {
                "alert_id": alert_id,
                "symbol": symbol,
                "current_price": current_price,
                "target_price": target_price,
                "alert_type": alert_type,
                "message": f"Alert triggered: {symbol} reached {current_price}",
                "triggered_at": datetime.utcnow().isoformat(),
            }
        }
        await self.send_personal_message(message, user_id)
        
        logger.info("alert_notification_sent", user_id=user_id, alert_id=alert_id)
    
    def get_active_users_count(self) -> int:
        """Get count of users with active connections"""
        return len(self.active_connections)
    
    def get_watching_users(self, symbol: str) -> Set[int]:
        """Get users watching a specific symbol"""
        return self.symbol_watchers.get(symbol.upper(), set())
    
    def get_stats(self) -> dict:
        """Get connection statistics"""
        return {
            "active_users": len(self.active_connections),
            "total_connections": sum(len(conns) for conns in self.active_connections.values()),
            "watched_symbols": len(self.symbol_watchers),
            "symbols": list(self.symbol_watchers.keys())
        }


# Global connection manager instance
manager = ConnectionManager()