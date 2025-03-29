import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
import logging


logger = logging.getLogger(__name__)

class MarketDataAnalyzer:
    """Analyzes market data to provide insights and intelligence"""
    
    def __init__(self, config, market_service=None):
        self.config = config
        self.market_service = market_service
    
    def set_market_service(self, market_service):
        """Set the market service after initialization"""
        self.market_service = market_service
    
    async def analyze_market_trend(self, symbol: str, days: int = 30) -> Dict[str, Any]:
        """Analyze market trend using moving averages"""
        if not self.market_service:
            logger.error("Market service not initialized")
            return {"error": "Market service not initialized"}
            
        historical_data = await self.market_service.get_historical_prices(symbol, days)
        
        if not historical_data:
            return {"trend": "unknown", "confidence": 0}
            
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(historical_data)
        
        # Calculate moving averages
        df['MA5'] = df['price'].rolling(window=5).mean()
        df['MA20'] = df['price'].rolling(window=20).mean()
        
        # Get the latest values
        latest = df.iloc[-1]
        
        # Determine trend
        if latest['MA5'] > latest['MA20']:
            trend = "bullish"
            # Calculate confidence based on difference
            confidence = min(100, (latest['MA5'] / latest['MA20'] - 1) * 1000)
        else:
            trend = "bearish"
            # Calculate confidence based on difference
            confidence = min(100, (latest['MA20'] / latest['MA5'] - 1) * 1000)
            
        return {
            "trend": trend,
            "confidence": round(confidence, 2),
            "current_price": latest['price'],
            "MA5": latest['MA5'],
            "MA20": latest['MA20']
        }
    
    async def calculate_volatility(self, symbol: str, days: int = 14) -> Dict[str, Any]:
        """Calculate volatility for a given asset"""
        if not self.market_service:
            logger.error("Market service not initialized")
            return {"error": "Market service not initialized"}
            
        historical_data = await self.market_service.get_historical_prices(symbol, days)
        
        if not historical_data:
            return {"volatility": 0, "risk_level": "unknown"}
            
        # Convert to DataFrame
        df = pd.DataFrame(historical_data)
        
        # Calculate daily returns
        df['returns'] = df['price'].pct_change()
        
        # Calculate volatility (standard deviation of returns)
        volatility = df['returns'].std() * np.sqrt(365) * 100  # Annualized volatility
        
        # Determine risk level
        if volatility < 30:
            risk_level = "low"
        elif volatility < 60:
            risk_level = "medium"
        else:
            risk_level = "high"
            
        return {
            "volatility": round(volatility, 2),
            "risk_level": risk_level,
            "daily_volatility": round(df['returns'].std() * 100, 2)
        }
    
    async def calculate_correlation(self, symbol1: str, symbol2: str, days: int = 30) -> Dict[str, Any]:
        """Calculate correlation between two assets"""
        if not self.market_service:
            logger.error("Market service not initialized")
            return {"error": "Market service not initialized"}
            
        data1 = await self.market_service.get_historical_prices(symbol1, days)
        data2 = await self.market_service.get_historical_prices(symbol2, days)
        
        if not data1 or not data2:
            return {"correlation": 0, "relationship": "unknown"}
            
        # Convert to DataFrames
        df1 = pd.DataFrame(data1)
        df2 = pd.DataFrame(data2)
        
        # Ensure they have the same dates
        merged = pd.merge(df1, df2, on='date', suffixes=('_1', '_2'))
        
        # Calculate correlation
        correlation = merged['price_1'].corr(merged['price_2'])
        
        # Determine relationship
        if correlation > 0.7:
            relationship = "strong positive"
        elif correlation > 0.3:
            relationship = "moderate positive"
        elif correlation > -0.3:
            relationship = "weak/none"
        elif correlation > -0.7:
            relationship = "moderate negative"
        else:
            relationship = "strong negative"
            
        return {
            "correlation": round(correlation, 2),
            "relationship": relationship,
            "sample_size": len(merged)
        }
    
    async def get_market_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Get market sentiment for a symbol (placeholder for now)"""
        # In a real implementation, this would use news API, social media, etc.
        import random
        
        sentiment_score = random.uniform(-1, 1)
        
        if sentiment_score > 0.3:
            sentiment = "positive"
        elif sentiment_score > -0.3:
            sentiment = "neutral"
        else:
            sentiment = "negative"
            
        return {
            "sentiment": sentiment,
            "score": round(sentiment_score, 2),
            "sources": ["simulated_data"]
        }
