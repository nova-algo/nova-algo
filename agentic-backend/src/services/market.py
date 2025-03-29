import aiohttp
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MarketDataService:
    """Service for fetching market data from various sources"""
    
    def __init__(self, config):
        self.config = config
        self.base_url = "https://pro-api.coinmarketcap.com/v1"
        self.api_key = config.CMC_API_KEY if hasattr(config, "CMC_API_KEY") else None
        self.cache = {}
        self.cache_timeout = 300  # Cache timeout in seconds (5 minutes)
        
    async def get_token_price(self, symbol: str) -> Optional[float]:
        """Get current price for a token by symbol"""
        try:
            data = await self._fetch_token_data(symbol)
            if data and symbol.upper() in data:
                return data[symbol.upper()].get("price", None)
            return None
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {str(e)}")
            return None
    
    async def get_token_data(self, symbol: str) -> Dict[str, Any]:
        """Get detailed token data including price, market cap, volume, etc."""
        return await self._fetch_token_data(symbol)
    
    async def get_market_overview(self) -> Dict[str, Any]:
        """Get overall market data (global market cap, BTC dominance, etc.)"""
        cache_key = "market_overview"
        
        # Check cache first
        if cache_key in self.cache:
            cache_time, cache_data = self.cache[cache_key]
            if datetime.now() - cache_time < timedelta(seconds=self.cache_timeout):
                return cache_data
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "X-CMC_PRO_API_KEY": self.api_key,
                    "Accept": "application/json"
                }
                
                url = f"{self.base_url}/global-metrics/quotes/latest"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        result = data.get("data", {})
                        
                        # Cache the result
                        self.cache[cache_key] = (datetime.now(), result)
                        return result
                    else:
                        logger.error(f"API error: {response.status}")
                        return {}
        except Exception as e:
            logger.error(f"Error fetching market overview: {str(e)}")
            return {}
    
    async def get_top_tokens(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get data for top tokens by market cap"""
        cache_key = f"top_tokens_{limit}"
        
        # Check cache first
        if cache_key in self.cache:
            cache_time, cache_data = self.cache[cache_key]
            if datetime.now() - cache_time < timedelta(seconds=self.cache_timeout):
                return cache_data
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "X-CMC_PRO_API_KEY": self.api_key,
                    "Accept": "application/json"
                }
                
                url = f"{self.base_url}/cryptocurrency/listings/latest?limit={limit}"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        result = data.get("data", [])
                        
                        # Cache the result
                        self.cache[cache_key] = (datetime.now(), result)
                        return result
                    else:
                        logger.error(f"API error: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error fetching top tokens: {str(e)}")
            return []
    
    async def _fetch_token_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch data for a specific token (internal helper)"""
        cache_key = f"token_{symbol.upper()}"
        
        # Check cache first
        if cache_key in self.cache:
            cache_time, cache_data = self.cache[cache_key]
            if datetime.now() - cache_time < timedelta(seconds=self.cache_timeout):
                return cache_data
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "X-CMC_PRO_API_KEY": self.api_key,
                    "Accept": "application/json"
                }
                
                url = f"{self.base_url}/cryptocurrency/quotes/latest?symbol={symbol.upper()}"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        result = data.get("data", {})
                        
                        # Cache the result
                        self.cache[cache_key] = (datetime.now(), result)
                        return result
                    else:
                        logger.error(f"API error: {response.status}")
                        return {}
        except Exception as e:
            logger.error(f"Error fetching token data for {symbol}: {str(e)}")
            return {}

    async def get_historical_prices(self, symbol: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get historical price data for a token"""
        cache_key = f"historical_{symbol.upper()}_{days}"
        
        # Check cache first
        if cache_key in self.cache:
            cache_time, cache_data = self.cache[cache_key]
            if datetime.now() - cache_time < timedelta(seconds=self.cache_timeout):
                return cache_data
        
        try:
            # For proper historical data, you might need a different API
            # This is a placeholder that returns dummy data
            result = await self._generate_dummy_historical_data(symbol, days)
            
            # Cache the result
            self.cache[cache_key] = (datetime.now(), result)
            return result
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            return []
    
    async def _generate_dummy_historical_data(self, symbol: str, days: int) -> List[Dict[str, Any]]:
        """Generate dummy historical data for demonstration purposes"""
        # In a real implementation, you would fetch this from an API
        import random
        
        # Try to get current price as baseline
        token_data = await self._fetch_token_data(symbol)
        base_price = 100  # Default if we can't get real price
        
        if token_data and symbol.upper() in token_data:
            price_data = token_data[symbol.upper()]
            if "quote" in price_data and "USD" in price_data["quote"]:
                base_price = price_data["quote"]["USD"]["price"]
        
        result = []
        now = datetime.now()
        
        for i in range(days):
            date = now - timedelta(days=days-i)
            # Generate a price with some randomness but trending toward current price
            price_factor = 0.8 + (0.4 * i / days) + (random.random() * 0.2)
            price = base_price * price_factor
            
            result.append({
                "date": date.strftime("%Y-%m-%d"),
                "price": round(price, 2),
                "volume": round(random.random() * base_price * 1000000, 2)
            })
        
        return result