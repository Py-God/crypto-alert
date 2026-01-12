# src/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Global application settings"""
    
    # Application
    APP_NAME: str = "Stock-Crypto-Alert-System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 300
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS - These will be parsed from comma-separated strings
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000"
    ALLOWED_METHODS: str = "GET,POST,PUT,DELETE,PATCH"
    ALLOWED_HEADERS: str = "*"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
    
    # Property methods to convert strings to lists
    @property
    def cors_origins(self) -> List[str]:
        """Convert comma-separated origins to list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    @property
    def cors_methods(self) -> List[str]:
        """Convert comma-separated methods to list"""
        return [method.strip() for method in self.ALLOWED_METHODS.split(",")]
    
    @property
    def cors_headers(self) -> List[str]:
        """Convert comma-separated headers to list"""
        if self.ALLOWED_HEADERS == "*":
            return ["*"]
        return [header.strip() for header in self.ALLOWED_HEADERS.split(",")]


# Create settings instance
settings = Settings()