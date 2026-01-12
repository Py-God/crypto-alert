from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from src.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,  # postgresql+asyncpg://user:pass@localhost/db
    pool_size=20,  # Keep 20 connections ready
    max_overflow=10,  # Allow 10 more if needed
    echo=settings.DEBUG,  # Log SQL queries in debug mode
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Don't expire objects after commit
)

Base = declarative_base()

# Dependency for routes
async def get_db() -> AsyncSession:
    """
    Creates a new database session for each request.
    Automatically closes when request is done.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session  # ← This is what Depends(get_db) gets
        finally:
            await session.close()