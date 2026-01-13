# src/market_data/service.py
from typing import Optional, Dict
from datetime import datetime
import structlog

from src.alerts.constants import AssetType
from src.market_data.client import market_data_client
from src.market_data.schemas import PriceData
from src.cache.redis_client import redis_client
from src.market_data.constants import PRICE_CACHE_TTL

logger = structlog.get_logger()


async def get_current_price(symbol: str, asset_type: AssetType) -> PriceData:
    """
    Get current price with caching
    
    Args:
        symbol: Asset symbol
        asset_type: "stock" or "crypto"
    
    Returns:
        PriceData object
    """
    symbol = symbol.upper()
    cache_key = f"price:{asset_type.value}:{symbol}"
    
    # DEBUG: Check if Redis is connected
    logger.info("checking_cache", 
                symbol=symbol, 
                cache_key=cache_key, 
                redis_connected=redis_client.is_connected())
    
    # Check cache
    try:
        cached_price = await redis_client.get(cache_key)
        if cached_price:
            logger.info("price_cache_hit", symbol=symbol, price=cached_price)
            return PriceData(
                symbol=symbol,
                asset_type=asset_type.value,
                price=float(cached_price),
                timestamp=datetime.utcnow(),
                source="cache"
            )
        else:
            logger.info("price_cache_miss", symbol=symbol)
    except Exception as e:
        logger.warning("cache_read_error", error=str(e))
    
    # Fetch from API
    logger.info("fetching_price_from_api", symbol=symbol)
    price = await market_data_client.get_price(symbol, asset_type)
    
    # Cache the result
    try:
        success = await redis_client.setex(cache_key, PRICE_CACHE_TTL, str(price))
        logger.info("cache_write_result", 
                   symbol=symbol, 
                   success=success, 
                   cache_key=cache_key,
                   price=price)
    except Exception as e:
        logger.warning("cache_write_error", error=str(e))
    
    # Determine source
    source = "binance" if asset_type == AssetType.CRYPTO else "yahoo"
    
    return PriceData(
        symbol=symbol,
        asset_type=asset_type.value,
        price=price,
        timestamp=datetime.utcnow(),
        source=source
    )


async def get_multiple_prices(
    symbols: list[str],
    asset_type: AssetType
) -> Dict[str, PriceData]:
    """
    Get multiple prices at once
    
    Args:
        symbols: List of symbols
        asset_type: Asset type for all symbols
    
    Returns:
        Dict of symbol -> PriceData
    """
    symbols_dict = {symbol: asset_type for symbol in symbols}
    prices = await market_data_client.get_multiple_prices(symbols_dict)
    
    result = {}
    for symbol, price in prices.items():
        source = "binance" if asset_type == AssetType.CRYPTO else "yahoo"
        result[symbol] = PriceData(
            symbol=symbol,
            asset_type=asset_type.value,
            price=price,
            timestamp=datetime.utcnow(),
            source=source
        )
    
    return result


async def validate_symbol(symbol: str, asset_type: AssetType) -> bool:
    """
    Validate if symbol exists
    
    Args:
        symbol: Asset symbol
        asset_type: Asset type
    
    Returns:
        True if valid
    """
    return await market_data_client.validate_symbol(symbol, asset_type)