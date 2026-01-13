# src/market_data/client.py
import asyncio
from typing import Optional, Dict
import httpx
import yfinance as yf
from datetime import datetime
import structlog

from src.alerts.constants import AssetType
from src.market_data.exceptions import SymbolNotFoundException, PriceDataUnavailableException
from src.market_data.constants import BINANCE_BASE_URL, COINGECKO_BASE_URL

logger = structlog.get_logger()


class MarketDataClient:
    """Client for fetching market data from various sources"""
    
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=10.0)
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()
    
    async def get_crypto_price_binance(self, symbol: str) -> Optional[float]:
        """
        Get crypto price from Binance
        
        Args:
            symbol: Crypto symbol (e.g., "BTC")
        
        Returns:
            Price in USD or None if not found
        """
        try:
            # Binance uses USDT pairs
            trading_pair = f"{symbol}USDT"
            
            url = f"{BINANCE_BASE_URL}/ticker/price"
            params = {"symbol": trading_pair}
            
            response = await self.http_client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                price = float(data['price'])
                logger.info("binance_price_fetched", symbol=symbol, price=price)
                return price
            elif response.status_code == 400:
                # Symbol not found
                return None
            else:
                logger.error("binance_api_error", status=response.status_code)
                return None
                
        except Exception as e:
            logger.error("binance_fetch_error", symbol=symbol, error=str(e))
            return None
    
    async def get_crypto_price_coingecko(self, symbol: str) -> Optional[float]:
        """
        Get crypto price from CoinGecko (backup)
        
        Args:
            symbol: Crypto symbol (e.g., "BTC")
        
        Returns:
            Price in USD or None if not found
        """
        try:
            # Map common symbols to CoinGecko IDs
            symbol_map = {
                "BTC": "bitcoin",
                "ETH": "ethereum",
                "BNB": "binancecoin",
                "ADA": "cardano",
                "SOL": "solana",
                "DOT": "polkadot",
                "DOGE": "dogecoin",
                "XRP": "ripple",
            }
            
            coin_id = symbol_map.get(symbol.upper())
            if not coin_id:
                return None
            
            url = f"{COINGECKO_BASE_URL}/simple/price"
            params = {"ids": coin_id, "vs_currencies": "usd"}
            
            response = await self.http_client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if coin_id in data:
                    price = float(data[coin_id]['usd'])
                    logger.info("coingecko_price_fetched", symbol=symbol, price=price)
                    return price
            
            return None
            
        except Exception as e:
            logger.error("coingecko_fetch_error", symbol=symbol, error=str(e))
            return None
    
    async def get_stock_price_yahoo(self, symbol: str) -> Optional[float]:
        """
        Get stock price from Yahoo Finance
        
        Args:
            symbol: Stock ticker (e.g., "AAPL")
        
        Returns:
            Price in USD or None if not found
        """
        try:
            # yfinance is synchronous, run in executor
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(None, yf.Ticker, symbol)
            info = await loop.run_in_executor(None, lambda: ticker.info)
            
            # Try different price fields
            price = (
                info.get('currentPrice') or
                info.get('regularMarketPrice') or
                info.get('previousClose')
            )
            
            if price is None:
                logger.warning("yahoo_no_price", symbol=symbol)
                return None
            
            price = float(price)
            logger.info("yahoo_price_fetched", symbol=symbol, price=price)
            return price
            
        except Exception as e:
            logger.error("yahoo_fetch_error", symbol=symbol, error=str(e))
            return None
    
    async def get_price(self, symbol: str, asset_type: AssetType) -> float:
        """
        Get current price for a symbol (with fallbacks)
        
        Args:
            symbol: Asset symbol
            asset_type: "stock" or "crypto"
        
        Returns:
            Current price
        
        Raises:
            SymbolNotFoundException: If symbol not found
            PriceDataUnavailableException: If price cannot be fetched
        """
        symbol = symbol.upper()
        
        if asset_type == AssetType.CRYPTO:
            # Try Binance first
            price = await self.get_crypto_price_binance(symbol)
            
            # Fallback to CoinGecko
            if price is None:
                price = await self.get_crypto_price_coingecko(symbol)
            
            if price is None:
                raise SymbolNotFoundException(symbol, "crypto")
            
            return price
        
        elif asset_type == AssetType.STOCK:
            # Use Yahoo Finance
            price = await self.get_stock_price_yahoo(symbol)
            
            if price is None:
                raise SymbolNotFoundException(symbol, "stock")
            
            return price
        
        else:
            raise ValueError(f"Unsupported asset type: {asset_type}")
    
    async def get_multiple_prices(self, symbols: Dict[str, AssetType]) -> Dict[str, float]:
        """
        Get prices for multiple symbols concurrently
        
        Args:
            symbols: Dict of {symbol: asset_type}
        
        Returns:
            Dict of {symbol: price}
        """
        tasks = [
            self.get_price(symbol, asset_type)
            for symbol, asset_type in symbols.items()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        prices = {}
        for symbol, result in zip(symbols.keys(), results):
            if isinstance(result, Exception):
                logger.error("price_fetch_failed", symbol=symbol, error=str(result))
                continue
            prices[symbol] = result
        
        return prices
    
    async def validate_symbol(self, symbol: str, asset_type: AssetType) -> bool:
        """
        Check if a symbol is valid and can be fetched
        
        Args:
            symbol: Asset symbol
            asset_type: "stock" or "crypto"
        
        Returns:
            True if symbol exists and can be fetched
        """
        try:
            await self.get_price(symbol, asset_type)
            return True
        except (SymbolNotFoundException, PriceDataUnavailableException):
            return False


# Global market data client instance
market_data_client = MarketDataClient()