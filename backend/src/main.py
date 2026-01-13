# src/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from pathlib import Path

from src.config import settings
from src.database import engine, Base
from src.cache.redis_client import redis_client

# Import monitoring
from src.monitoring.scheduler import start_scheduler, stop_scheduler

# Import routers
from src.auth.router import router as auth_router
from src.alerts.router import router as alerts_router
from src.market_data.router import router as market_data_router
from src.websocket.router import router as websocket_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("🚀 Starting application...")
    
    # Initialize database
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database initialized")
    
    # Connect to Redis
    await redis_client.connect()
    if redis_client.is_connected():
        print("✅ Redis connected")
    else:
        print("⚠️  Redis connection failed - running without cache")
    
    # Start background monitoring
    await start_scheduler()  # ← Add this
    print("✅ Background monitoring started")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down application...")
    
    # Stop monitoring
    await stop_scheduler()  # ← Add this
    print("✅ Background monitoring stopped")
    
    # Disconnect Redis
    await redis_client.disconnect()
    
    # Dispose database engine
    await engine.dispose()
    
    print("✅ Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Real-Time Stock/Crypto Price Alert System",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)


# Health check
@app.get("/")
async def root():
    return {
        "message": "Stock/Crypto Alert System API",
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "redis_connected": redis_client.is_connected()
    }


@app.get("/ws-test", response_class=HTMLResponse)
async def websocket_test_page():
    """WebSocket test page"""
    html_path = Path("templates/websocket_test.html")
    if html_path.exists():
        return html_path.read_text()
    return "<h1>Test page not found</h1>"


# Include routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(alerts_router, prefix="/api/v1/alerts", tags=["Alerts"])
app.include_router(market_data_router, prefix="/api/v1/market", tags=["Market Data"])
app.include_router(websocket_router, prefix="/api/v1/ws", tags=["WebSocket"])


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )