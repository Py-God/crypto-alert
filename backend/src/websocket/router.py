# src/websocket/router.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional
import structlog

from src.websocket.manager import manager
from src.auth.dependencies import get_current_user
from src.auth.models import User

router = APIRouter()
logger = structlog.get_logger()


async def get_current_user_ws(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
) -> Optional[int]:
    """
    Get current user from WebSocket token
    
    WebSocket connections pass token as query parameter:
    ws://localhost:8000/api/v1/ws/connect?token=YOUR_ACCESS_TOKEN
    """
    if not token:
        await websocket.close(code=1008, reason="Missing authentication token")
        return None
    
    try:
        from src.auth.service import decode_token
        from src.database import AsyncSessionLocal
        from src.auth import service
        
        # Decode token
        payload = decode_token(token)
        if not payload:
            await websocket.close(code=1008, reason="Invalid token")
            return None
        
        user_id = payload.get("sub")
        token_type = payload.get("type")
        
        if not user_id or token_type != "access":
            await websocket.close(code=1008, reason="Invalid token type")
            return None
        
        # Verify user exists
        async with AsyncSessionLocal() as db:
            user = await service.get_user_by_id(db, int(user_id))
            if not user or not user.is_active:
                await websocket.close(code=1008, reason="User not found or inactive")
                return None
        
        return int(user_id)
        
    except Exception as e:
        logger.error("websocket_auth_error", error=str(e))
        await websocket.close(code=1011, reason="Authentication failed")
        return None


@router.websocket("/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for real-time updates
    
    Connection URL: ws://localhost:8000/api/v1/ws/connect?token=YOUR_ACCESS_TOKEN
    
    **Message Types:**
    
    Client → Server:
    - `{"type": "subscribe", "symbol": "BTC"}` - Subscribe to BTC price updates
    - `{"type": "unsubscribe", "symbol": "BTC"}` - Unsubscribe from BTC
    - `{"type": "ping"}` - Keepalive ping
    - `{"type": "get_subscriptions"}` - Get list of subscribed symbols
    
    Server → Client:
    - `{"type": "connected", ...}` - Connection successful
    - `{"type": "price_update", "data": {...}}` - Price update for subscribed symbol
    - `{"type": "alert_triggered", "data": {...}}` - Alert was triggered
    - `{"type": "pong"}` - Response to ping
    - `{"type": "subscriptions", "data": [...]}` - List of subscriptions
    - `{"type": "error", "message": "..."}` - Error message
    """
    
    # Authenticate user
    user_id = await get_current_user_ws(websocket, token)
    if not user_id:
        return
    
    # Connect
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            message_type = data.get("type")
            
            if message_type == "subscribe":
                # Subscribe to symbol
                symbol = data.get("symbol", "").upper()
                if symbol:
                    manager.subscribe_to_symbol(user_id, symbol)
                    await websocket.send_json({
                        "type": "subscribed",
                        "symbol": symbol,
                        "message": f"Subscribed to {symbol} updates"
                    })
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Symbol is required"
                    })
            
            elif message_type == "unsubscribe":
                # Unsubscribe from symbol
                symbol = data.get("symbol", "").upper()
                if symbol:
                    manager.unsubscribe_from_symbol(user_id, symbol)
                    await websocket.send_json({
                        "type": "unsubscribed",
                        "symbol": symbol,
                        "message": f"Unsubscribed from {symbol} updates"
                    })
            
            elif message_type == "get_subscriptions":
                # Get user's subscriptions
                subscriptions = manager.get_user_subscriptions(user_id)
                await websocket.send_json({
                    "type": "subscriptions",
                    "data": subscriptions
                })
            
            elif message_type == "ping":
                # Respond to ping
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": data.get("timestamp")
                })
            
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("websocket_client_disconnected", user_id=user_id)
    except Exception as e:
        logger.error("websocket_error", user_id=user_id, error=str(e))
        manager.disconnect(websocket)


@router.get("/stats")
async def get_websocket_stats(
    current_user: User = Depends(get_current_user)
):
    """
    Get WebSocket connection statistics
    
    Requires authentication.
    """
    return manager.get_stats()