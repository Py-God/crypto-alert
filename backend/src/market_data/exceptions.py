# src/market_data/exceptions.py
from fastapi import HTTPException, status


class MarketDataException(HTTPException):
    """Base exception for market data errors"""
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


class SymbolNotFoundException(MarketDataException):
    """Raised when symbol is not found"""
    def __init__(self, symbol: str, asset_type: str):
        super().__init__(
            detail=f"{asset_type.upper()} symbol '{symbol}' not found or not supported",
            status_code=status.HTTP_404_NOT_FOUND
        )


class PriceDataUnavailableException(MarketDataException):
    """Raised when price data cannot be fetched"""
    def __init__(self, symbol: str, reason: str = ""):
        detail = f"Price data unavailable for '{symbol}'"
        if reason:
            detail += f": {reason}"
        super().__init__(detail=detail, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


class RateLimitExceededException(MarketDataException):
    """Raised when API rate limit is exceeded"""
    def __init__(self):
        super().__init__(
            detail="Rate limit exceeded. Please try again later.",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )