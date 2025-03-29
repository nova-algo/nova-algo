import asyncio
import aiohttp
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

class AlloraClient:
    """Client for interacting with Allora Network APIs"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.allora.network"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = None
        self.topic_map = {
            # Short-term predictions (5min)
            "ETH_5min": 13,
            "BTC_5min": 14,
            "ETH_5min_volatility": 15,
            "BTC_5min_volatility": 16,
            
            # Medium-term predictions
            "ETH_10min": 1,
            "BTC_10min": 3,
            "SOL_10min": 5,
            "ETH_20min": 7,
            "BNB_20min": 8,
            "ARB_20min": 9,
            
            # Long-term predictions (24h)
            "ETH_24h": 2,
            "BTC_24h": 4,
            "SOL_24h": 6,
            
            # Special topics
            "MEME_1h": 10
        }
        # Add caching to reduce API calls
        self.cache = {}
        self.cache_expiry = {}
        self.default_cache_ttl = 300  # 5 minutes in seconds
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers={
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def get_prediction(self, topic_id: int) -> Dict[str, Any]:
        """
        Get the latest prediction for a specific topic
        
        Args:
            topic_id: The Allora topic ID (e.g., 14 for BTC, 13 for ETH)
            
        Returns:
            Dictionary containing prediction data
        """
        # Check cache first
        cache_key = f"prediction_{topic_id}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data

        if not self.session:
            self.session = aiohttp.ClientSession(headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            })
            
        url = f"{self.base_url}/v1/topics/{topic_id}/predictions/latest"
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    result = await response.json()
                    # Add to cache with default TTL
                    self._add_to_cache(cache_key, result)
                    return result
                elif response.status == 429:  # Rate limited
                    # Implement exponential backoff
                    await asyncio.sleep(2)
                    return await self.get_prediction(topic_id)
                else:
                    error_text = await response.text()
                    raise Exception(f"Failed to get prediction: {error_text}")
        except aiohttp.ClientError as e:
            raise Exception(f"Network error: {str(e)}")
                
    async def get_market_sentiment(self, asset: str) -> Dict[str, Any]:
        """
        Get market sentiment analysis for an asset
        
        Args:
            asset: Asset symbol (e.g., "BTC")
            
        Returns:
            Dictionary with market sentiment data
        """
        # Check cache first
        cache_key = f"sentiment_{asset}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data
            
        # Map assets to topic IDs for sentiment
        topic_key = f"{asset}_5min"
        if topic_key not in self.topic_map:
            raise ValueError(f"No topic found for {asset}")
        
        topic_id = self.topic_map[topic_key]
        prediction = await self.get_prediction(topic_id)
        
        # Extract sentiment information
        sentiment_data = self._extract_sentiment_from_prediction(prediction, asset)
        
        # Cache the result
        self._add_to_cache(cache_key, sentiment_data)
        
        return sentiment_data
        
    def _extract_sentiment_from_prediction(self, prediction: Dict[str, Any], asset: str) -> Dict[str, Any]:
        """
        Extract sentiment information from a prediction
        
        Implements Rose Heart's advice to focus on fear/greed and emotional patterns
        """
        # Get the prediction value and timestamp
        value = prediction.get("value", 0)
        timestamp = prediction.get("timestamp", "")
        
        # Get previous value if available
        prev_value = prediction.get("previous_value", value)
        
        # Calculate sentiment based on prediction movement
        sentiment = "neutral"
        if value > prev_value * 1.02:  # 2% increase
            sentiment = "bullish"
        elif value < prev_value * 0.98:  # 2% decrease
            sentiment = "bearish"
            
        # Calculate fear/greed score
        # Rose Heart emphasized this as a key emotional indicator
        price_change_pct = ((value - prev_value) / prev_value) if prev_value else 0
        
        fear_score = 0.5  # Neutral starting point
        greed_score = 0.5
        
        # Adjust based on prediction movement
        if price_change_pct > 0:
            # Positive prediction indicates greed
            adjustment = min(0.4, price_change_pct * 2)  # Cap at 0.4
            greed_score += adjustment
            fear_score -= adjustment
        else:
            # Negative prediction indicates fear
            adjustment = min(0.4, abs(price_change_pct) * 2)  # Cap at 0.4
            fear_score += adjustment
            greed_score -= adjustment
            
        # Ensure scores are in 0-1 range
        fear_score = max(0, min(1, fear_score))
        greed_score = max(0, min(1, greed_score))
        
        # Detection of potential market manipulation
        # Rose Heart emphasized checking for manipulation
        predicted_change = abs(price_change_pct)
        manipulation_score = 0.0
        
        # Sudden large movements may indicate manipulation
        if predicted_change > 0.1:  # 10% change
            manipulation_score = min(1.0, predicted_change * 2)
            
        return {
            "asset": asset,
            "sentiment": sentiment,
            "fear_score": fear_score,
            "greed_score": greed_score,
            "primary_emotion": "fear" if fear_score > greed_score else "greed",
            "manipulation_detected": manipulation_score > 0.6,
            "manipulation_score": manipulation_score,
            "timestamp": timestamp
        }

    async def analyze_sentiment(self, asset: str, content: str = None) -> Dict[str, Any]:
        """
        Analyze sentiment for an asset from content (news, social media, etc.)
        
        Following Rose Heart's advice, this focuses ONLY on sentiment/emotion analysis
        
        Args:
            asset: Asset symbol (e.g., "BTC")
            content: Text content to analyze. If None, will use market data.
            
        Returns:
            Dictionary with sentiment analysis and fear/greed classification
        """
        # If no content provided, use market sentiment
        if not content:
            return await self.get_market_sentiment(asset)
            
        cache_key = f"text_sentiment_{asset}_{hash(content)}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data
            
        if not self.session:
            self.session = aiohttp.ClientSession(headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            })
            
        url = f"{self.base_url}/v1/sentiment/analyze"
        try:
            async with self.session.post(url, json={
                "asset": asset,
                "content": content
            }) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Extract fear/greed signals as Rose Heart suggested
                    fear_score = result.get("fear_score", 0.5)
                    greed_score = result.get("greed_score", 0.5)
                    
                    # Check for manipulation attempts (Rose Heart's advice)
                    manipulation_score = result.get("manipulation_score", 0.0)
                    
                    sentiment_data = {
                        "asset": asset,
                        "sentiment": result.get("sentiment", "neutral"),
                        "fear_score": fear_score,
                        "greed_score": greed_score,
                        "manipulation_detected": manipulation_score > 0.6,
                        "manipulation_score": manipulation_score,
                        "primary_emotion": "fear" if fear_score > greed_score else "greed",
                        "confidence": result.get("confidence", 0.5),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Add to cache with longer TTL for text analysis
                    self._add_to_cache(cache_key, sentiment_data, 1800)  # 30 minutes
                    
                    return sentiment_data
                else:
                    error_text = await response.text()
                    raise Exception(f"Failed to analyze sentiment: {error_text}")
        except Exception as e:
            # Fallback to market sentiment if text analysis fails
            return await self.get_market_sentiment(asset)

    async def get_topic_prediction(self, topic_key: str, arg: Optional[str] = None) -> Dict[str, Any]:
        """
        Get prediction from an Allora topic
        
        Args:
            topic_key: Key from topic_map (e.g., "ETH_5min")
            arg: Optional argument to pass to the topic
        """
        if topic_key not in self.topic_map:
            raise ValueError(f"Unknown topic key: {topic_key}")
            
        topic_id = self.topic_map[topic_key]
        
        # Use default arg if none provided
        if arg is None:
            # Default args based on the topic documentation
            default_args = {
                "ETH_5min": "ETH",
                "BTC_5min": "BTC",
                "ETH_10min": "ETH",
                # ... add others as needed
            }
            arg = default_args.get(topic_key, "")
            
        return await self.get_prediction(topic_id)
        
    def _add_to_cache(self, key: str, data: Any, ttl: int = None):
        """Add data to cache with expiry time"""
        if ttl is None:
            ttl = self.default_cache_ttl
            
        self.cache[key] = data
        self.cache_expiry[key] = time.time() + ttl
        
    def _get_from_cache(self, key: str) -> Any:
        """Get data from cache if not expired"""
        if key in self.cache and time.time() < self.cache_expiry.get(key, 0):
            return self.cache[key]
        return None

    async def get_fear_greed_index(self, asset: str) -> Dict[str, Any]:
        """
        Get the fear/greed index for an asset
        
        Rose Heart emphasized fear/greed as a key indicator for crypto
        
        Args:
            asset: Asset symbol (e.g., "BTC")
            
        Returns:
            Dictionary with fear/greed index and classification
        """
        sentiment_data = await self.get_market_sentiment(asset)
        
        # Extract relevant data
        fear_score = sentiment_data.get("fear_score", 0.5)
        greed_score = sentiment_data.get("greed_score", 0.5)
        
        # Calculate index value (0-100)
        # 0 = Extreme Fear, 100 = Extreme Greed
        index_value = int(greed_score * 100)
        
        # Determine classification
        classification = "Neutral"
        if index_value < 25:
            classification = "Extreme Fear"
        elif index_value < 40:
            classification = "Fear"
        elif index_value < 60:
            classification = "Neutral"
        elif index_value < 80:
            classification = "Greed"
        else:
            classification = "Extreme Greed"
            
        return {
            "asset": asset,
            "fear_greed_index": index_value,
            "classification": classification,
            "timestamp": datetime.now().isoformat()
        }
        
    async def detect_market_manipulation(self, asset: str) -> Dict[str, Any]:
        """
        Detect potential market manipulation for an asset
        
        Rose Heart specifically cautioned about manipulation in newer markets
        
        Args:
            asset: Asset symbol (e.g., "BTC")
            
        Returns:
            Dictionary with manipulation assessment
        """
        sentiment_data = await self.get_market_sentiment(asset)
        
        manipulation_score = sentiment_data.get("manipulation_score", 0.0)
        manipulation_detected = manipulation_score > 0.6
        
        risk_level = "Low"
        if manipulation_score > 0.8:
            risk_level = "High"
        elif manipulation_score > 0.6:
            risk_level = "Medium"
            
        return {
            "asset": asset,
            "manipulation_detected": manipulation_detected,
            "manipulation_score": manipulation_score,
            "risk_level": risk_level,
            "timestamp": datetime.now().isoformat()
        }
