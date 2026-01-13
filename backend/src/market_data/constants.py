# src/market_data/constants.py

# Supported asset types
SUPPORTED_CRYPTO = ["BTC", "ETH", "BNB", "ADA", "SOL", "DOT", "DOGE", "XRP", "USDT", "USDC"]
SUPPORTED_STOCKS = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "AMD"]

# API endpoints
BINANCE_BASE_URL = "https://api.binance.com/api/v3"
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"

# Cache settings
PRICE_CACHE_TTL = 5  # seconds
SYMBOL_INFO_CACHE_TTL = 3600  # 1 hour

# Rate limiting
MAX_REQUESTS_PER_MINUTE = 100