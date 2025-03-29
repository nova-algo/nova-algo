import asyncio
import logging
from typing import Dict, List, Any
import pandas as pd

logger = logging.getLogger(__name__)

class MarketMonitor:
    """
    Monitors overall market conditions and sentiment.
    
    Following Rose Heart's advice, this focuses on broad market metrics
    to inform the rebalancing strategy but does not execute trades.
    """
    
    def __init__(self, market_data_service, allora_client):
        self.market_data_service = market_data_service
        self.allora_client = allora_client
        self.market_metrics = {}
        
    async def start_monitoring(self, assets: List[str], interval_seconds: int = 300):
        """Start continuous market monitoring"""
        while True:
            try:
                await self.update_market_metrics(assets)
                logger.info(f"Updated market metrics for {len(assets)} assets")
            except Exception as e:
                logger.error(f"Error updating market metrics: {str(e)}")
            
            await asyncio.sleep(interval_seconds)
    
    async def update_market_metrics(self, assets: List[str]):
        """Update market metrics for tracked assets"""
        for asset in assets:
            try:
                # Get market data
                market_data = await self.market_data_service.get_market_data(asset)
                
                # Get sentiment analysis (as before)
                social_content = await self.market_data_service.get_social_content(asset)
                sentiment = await self.allora_client.analyze_sentiment(asset, social_content)
                
                # NEW: Get Allora price predictions
                predictions = await self.get_price_predictions(asset)
                
                # Calculate statistical metrics (as before)
                price_data = pd.DataFrame(market_data.get("prices", []))
                if not price_data.empty:
                    # Statistical calculations (unchanged)
                    median_price = price_data["price"].median()
                    below_median_freq = (price_data["price"] < median_price).mean()
                    volatility = price_data["price"].pct_change().std() * (365 ** 0.5)
                    
                    # Check for market manipulation - Rose Heart emphasized this
                    is_manipulated = await self._check_for_manipulation(asset, price_data)
                    
                    # Store metrics with predictions
                    self.market_metrics[asset] = {
                        "updated_at": pd.Timestamp.now().isoformat(),
                        "price": market_data.get("current_price", 0),
                        "sentiment": sentiment.get("primary_emotion", "neutral"),
                        "fear_score": sentiment.get("fear_score", 0.5),
                        "greed_score": sentiment.get("greed_score", 0.5),
                        "manipulation_detected": sentiment.get("manipulation_detected", False) or is_manipulated,
                        "below_median_frequency": float(below_median_freq),
                        "volatility": float(volatility),
                        "market_status": self._determine_market_status(sentiment, below_median_freq, volatility),
                        "predictions": {
                            "short_term": self._extract_prediction(predictions, f"{asset}_5min"),
                            "medium_term": self._extract_prediction(predictions, f"{asset}_20min") or 
                                          self._extract_prediction(predictions, f"{asset}_10min"),
                            "long_term": self._extract_prediction(predictions, f"{asset}_24h"),
                            "volatility": self._extract_prediction(predictions, f"{asset}_5min_volatility")
                        }
                    }
            except Exception as e:
                logger.error(f"Error updating metrics for {asset}: {str(e)}")
    
    async def _check_for_manipulation(self, asset: str, price_data: pd.DataFrame) -> bool:
        """
        Check for potential market manipulation
        
        Rose Heart emphasized this especially for newer/lower-value assets
        """
        if len(price_data) < 50:
            return False
            
        # Look for sudden price movements
        returns = price_data["price"].pct_change().dropna()
        
        # Check for large price swings
        large_swings = (returns.abs() > 0.1).sum()
        
        # Check for unusual volume spikes (if volume data available)
        volume_spikes = 0
        if "volume" in price_data.columns:
            volume = price_data["volume"]
            avg_volume = volume.mean()
            volume_spikes = (volume > avg_volume * 3).sum()
        
        # Combine indicators
        return large_swings > 3 or volume_spikes > 2
    
    def _determine_market_status(self, sentiment, below_median_freq, volatility):
        """Determine overall market status based on metrics"""
        # Start with sentiment
        if sentiment.get("primary_emotion") == "fear" and sentiment.get("fear_score", 0) > 0.7:
            return "extreme_fear"
        elif sentiment.get("primary_emotion") == "greed" and sentiment.get("greed_score", 0) > 0.7:
            return "extreme_greed"
        
        # Check statistical metrics
        if below_median_freq > 0.7:
            return "oversold"
        elif below_median_freq < 0.3:
            return "overbought"
        
        # Check volatility
        if volatility > 0.8:
            return "high_volatility"
        elif volatility < 0.2:
            return "low_volatility"
        
        return "normal"
    
    def get_market_metrics(self, asset: str) -> Dict[str, Any]:
        """Get current market metrics for an asset"""
        return self.market_metrics.get(asset, {})
    
    def get_consolidated_market_view(self) -> Dict[str, Any]:
        """Get consolidated view of market conditions across all assets"""
        if not self.market_metrics:
            return {"status": "unknown", "message": "No market data available"}
        
        # Count assets in each market status
        status_counts = {}
        for asset, metrics in self.market_metrics.items():
            status = metrics.get("market_status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Calculate average fear/greed scores
        avg_fear = sum(m.get("fear_score", 0.5) for m in self.market_metrics.values()) / len(self.market_metrics)
        avg_greed = sum(m.get("greed_score", 0.5) for m in self.market_metrics.values()) / len(self.market_metrics)
        
        # Count manipulated assets
        manipulation_count = sum(1 for m in self.market_metrics.values() if m.get("manipulation_detected", False))
        
        # Determine overall market status
        if "extreme_fear" in status_counts and status_counts["extreme_fear"] > len(self.market_metrics) * 0.3:
            overall_status = "fearful"
        elif "extreme_greed" in status_counts and status_counts["extreme_greed"] > len(self.market_metrics) * 0.3:
            overall_status = "greedy"
        elif "high_volatility" in status_counts and status_counts["high_volatility"] > len(self.market_metrics) * 0.3:
            overall_status = "volatile"
        elif manipulation_count > len(self.market_metrics) * 0.2:
            overall_status = "suspicious"
        else:
            overall_status = "normal"
        
        return {
            "status": overall_status,
            "asset_count": len(self.market_metrics),
            "status_distribution": status_counts,
            "average_fear_score": avg_fear,
            "average_greed_score": avg_greed,
            "manipulation_detected_count": manipulation_count,
            "updated_at": pd.Timestamp.now().isoformat()
        }
    
    async def get_trading_recommendations(self) -> List[Dict[str, Any]]:
        """
        Get trading recommendations based on market metrics
        
        Follows Rose Heart's approach of combining sentiment with statistics
        """
        recommendations = []
        
        for asset, metrics in self.market_metrics.items():
            # Skip assets with potential manipulation
            if metrics.get("manipulation_detected", False):
                recommendations.append({
                    "asset": asset,
                    "action": "avoid",
                    "confidence": 80,
                    "reason": "Potential market manipulation detected"
                })
                continue
            
            # Combine sentiment and statistical signals with equal weight
            # as Rose Heart suggested
            
            # Sentiment signal
            sentiment = metrics.get("sentiment", "neutral")
            fear_score = metrics.get("fear_score", 0.5)
            greed_score = metrics.get("greed_score", 0.5)
            
            sentiment_signal = 0
            if sentiment == "fear" and fear_score > 0.6:
                sentiment_signal = 1  # Buy on fear (contrarian)
            elif sentiment == "greed" and greed_score > 0.6:
                sentiment_signal = -1  # Sell on greed (contrarian)
            
            # Statistical signal
            below_median = metrics.get("below_median_frequency", 0.5)
            volatility = metrics.get("volatility", 0.5)
            
            stat_signal = 0
            if below_median > 0.7:
                stat_signal = 1  # Buy when price is frequently below median
            elif below_median < 0.3:
                stat_signal = -1  # Sell when price is rarely below median
                
            # Adjust for volatility - be more cautious with volatile assets
            if volatility > 0.7:
                stat_signal *= 0.7
            
            # Combine signals with equal weight (Rose Heart's advice)
            combined_signal = (sentiment_signal + stat_signal) / 2
            
            # Determine action
            action = "hold"
            confidence = 50
            reason = "No strong signals"
            
            if combined_signal > 0.3:
                action = "buy"
                confidence = int(min(combined_signal * 100, 90))
                reason = f"Positive sentiment ({sentiment}) and statistical indicators ({below_median:.2f} below median)"
            elif combined_signal < -0.3:
                action = "sell"
                confidence = int(min(abs(combined_signal) * 100, 90))
                reason = f"Negative sentiment ({sentiment}) and statistical indicators ({below_median:.2f} below median)"
            
            recommendations.append({
                "asset": asset,
                "action": action,
                "confidence": confidence,
                "reason": reason,
                "sentiment_signal": sentiment_signal,
                "statistical_signal": stat_signal,
                "combined_signal": combined_signal
            })
        
        # Sort by confidence
        recommendations.sort(key=lambda x: x["confidence"], reverse=True)
        
        return recommendations

    async def get_price_predictions(self, asset: str) -> Dict[str, Any]:
        """
        Get multi-timeframe price predictions for an asset
        using Allora's existing topics
        """
        result = {}
        
        # Map assets to Allora topics
        asset_topics = {
            "ETH": ["ETH_5min", "ETH_10min", "ETH_20min", "ETH_24h", "ETH_5min_volatility"],
            "BTC": ["BTC_5min", "BTC_10min", "BTC_24h", "BTC_5min_volatility"],
            "SOL": ["SOL_10min", "SOL_24h"],
            "BNB": ["BNB_20min"],
            "ARB": ["ARB_20min"]
        }
        
        # Get topics for this asset
        topics = asset_topics.get(asset, [])
        
        # If no specific topics, return empty result
        if not topics:
            return result
        
        # Get predictions for each timeframe
        for topic in topics:
            try:
                prediction = await self.allora_client.get_topic_prediction(topic)
                result[topic] = prediction
            except Exception as e:
                logger.error(f"Error getting prediction for {topic}: {str(e)}")
            
        return result

    def _extract_prediction(self, predictions, key):
        """Extract prediction value from Allora response"""
        if key not in predictions:
            return None
        
        prediction = predictions[key]
        return {
            "direction": "up" if prediction.get("value", 0) > 0 else "down",
            "confidence": prediction.get("confidence", 0),
            "value": prediction.get("value", 0),
            "timestamp": prediction.get("timestamp")
        }
