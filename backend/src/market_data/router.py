# src/market_data/router.py
from fastapi import APIRouter, Query, HTTPException, status
from typing import Optional

from src.alerts.constants import AssetType
from src.market_data import service, schemas
from src.market_data.exceptions import SymbolNotFoundException, PriceDataUnavailableException

router = APIRouter()


@router.get(
    "/price/{symbol}",
    response_model=schemas.PriceData,
    summary="Get current price for a symbol"
)
async def get_price(
    symbol: str,
    asset_type: AssetType = Query(..., description="Asset type: stock or crypto")
):
    """
    Get the current price for a stock or cryptocurrency.
    
    - **symbol**: Stock ticker (e.g., AAPL) or crypto symbol (e.g., BTC)
    - **asset_type**: Either "stock" or "crypto"
    
    Returns current price with timestamp and source.
    
    **Examples:**
    - `/price/BTC?asset_type=crypto` - Get Bitcoin price
    - `/price/AAPL?asset_type=stock` - Get Apple stock price
    """
    try:
        price_data = await service.get_current_price(symbol, asset_type)
        return price_data
    except SymbolNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.detail))
    except PriceDataUnavailableException as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e.detail))


@router.post(
    "/prices",
    response_model=schemas.MultiplePricesResponse,
    summary="Get prices for multiple symbols"
)
async def get_multiple_prices(request: schemas.MultiplePricesRequest):
    """
    Get current prices for multiple symbols at once.
    
    Useful for fetching prices for a watchlist or portfolio.
    
    **Request Body:**
```json
    {
      "symbols": ["BTC", "ETH", "BNB"],
      "asset_type": "crypto"
    }
```
    
    Returns prices for all requested symbols.
    """
    try:
        asset_type = AssetType(request.asset_type)
        prices = await service.get_multiple_prices(request.symbols, asset_type)
        
        return schemas.MultiplePricesResponse(prices=prices)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/validate/{symbol}",
    summary="Validate if a symbol exists"
)
async def validate_symbol(
    symbol: str,
    asset_type: AssetType = Query(..., description="Asset type: stock or crypto")
):
    """
    Check if a symbol is valid and can be fetched.
    
    Useful for validating user input before creating alerts.
    
    Returns:
```json
    {
      "symbol": "BTC",
      "asset_type": "crypto",
      "valid": true
    }
```
    """
    is_valid = await service.validate_symbol(symbol, asset_type)
    
    return {
        "symbol": symbol.upper(),
        "asset_type": asset_type.value,
        "valid": is_valid
    }