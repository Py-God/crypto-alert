# src/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings

# Import auth router - THIS IS CRUCIAL
from src.auth.router import router as auth_router

# Create app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Real-Time Stock/Crypto Price Alert System",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Stock/Crypto Alert System API",
        "version": settings.APP_VERSION,
        "status": "running"
    }

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
    }

# INCLUDE AUTH ROUTER - THIS LINE IS CRITICAL
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])

# Add this line for debugging
@app.on_event("startup")
async def startup_event():
    print("✅ App started")
    print(f"📋 Registered routes:")
    for route in app.routes:
        print(f"  {route.path}")