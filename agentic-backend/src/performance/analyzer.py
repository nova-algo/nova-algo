"""
Performance Analyzer

Analyzes the effectiveness of rebalancing strategies and sentiment analysis.
Inspired by the performance analysis in the Allora HyperLiquid AutoTradeBot.
"""
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class TradeLog(BaseModel):
    """Log entry for a trade or rebalancing action"""
    portfolio_id: int
    asset: str
    action: str  # "increase", "decrease", "maintain"
    timestamp: str
    entry_price: float
    amount: float
    value: float
    sentiment: str  # "fear", "greed", "neutral"
    manipulation_detected: bool = False
    volatility: float
    market_condition: str
    allora_signal: str  # "bullish", "bearish", "neutral"
    statistical_signal: str  # "increase", "decrease", "maintain"
    confidence: float
    exit_price: Optional[float] = None
    exit_timestamp: Optional[str] = None
    profit_loss: Optional[float] = None
    profit_loss_percent: Optional[float] = None

class PerformanceAnalyzer:
    """
    Analyzes the performance of rebalancing strategies and AI signals.
    
    Tracks:
    - Sentiment signal accuracy
    - Statistical signal accuracy
    - Combined signal accuracy
    - Market condition impact
    - Correlation between signals and outcomes
    """
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        
    async def log_rebalance(self, rebalance_data: Dict[str, Any]) -> None:
        """Log a rebalancing action for future analysis"""
        try:
            # Extract data
            portfolio_id = rebalance_data.get("portfolio_id")
            timestamp = rebalance_data.get("timestamp", datetime.now().isoformat())
            assets = rebalance_data.get("assets", [])
            
            # Log each trade
            for asset in assets:
                rebalance_signal = asset.get("rebalance_signal", {})
                sentiment = asset.get("sentiment", {})
                stats = asset.get("statistical", {})
                
                log_entry = TradeLog(
                    portfolio_id=portfolio_id,
                    asset=asset.get("asset"),
                    action=rebalance_signal.get("action", "maintain"),
                    timestamp=timestamp,
                    entry_price=asset.get("current_price", 0),
                    amount=rebalance_signal.get("amount", 0),
                    value=rebalance_signal.get("value", 0),
                    sentiment=sentiment.get("primary_emotion", "neutral"),
                    manipulation_detected=asset.get("manipulation", {}).get("manipulation_detected", False),
                    volatility=stats.get("volatility", 0),
                    market_condition=rebalance_data.get("market_condition", "normal"),
                    allora_signal=sentiment.get("sentiment", "neutral"),
                    statistical_signal=stats.get("statistical_signal", "maintain"),
                    confidence=rebalance_signal.get("confidence", 0.5)
                )
                
                await self._save_trade_log(log_entry)
                
        except Exception as e:
            logger.error(f"Error logging rebalance: {str(e)}")
    
    async def update_trade_outcome(self, log_id: int, exit_price: float) -> None:
        """Update a trade log with the outcome"""
        try:
            # Get the log entry
            log_entry = await self._get_trade_log(log_id)
            if not log_entry:
                logger.error(f"Trade log {log_id} not found")
                return
                
            # Update with exit data
            log_entry.exit_price = exit_price
            log_entry.exit_timestamp = datetime.now().isoformat()
            
            # Calculate profit/loss
            if log_entry.action == "increase":
                # Buying - profit if price goes up
                profit_loss = (exit_price - log_entry.entry_price) * log_entry.amount
                profit_loss_percent = (exit_price - log_entry.entry_price) / log_entry.entry_price
            elif log_entry.action == "decrease":
                # Selling - profit if price goes down
                profit_loss = (log_entry.entry_price - exit_price) * log_entry.amount
                profit_loss_percent = (log_entry.entry_price - exit_price) / log_entry.entry_price
            else:
                # Maintaining - no action
                profit_loss = 0
                profit_loss_percent = 0
                
            log_entry.profit_loss = profit_loss
            log_entry.profit_loss_percent = profit_loss_percent
            
            await self._update_trade_log(log_entry)
            
        except Exception as e:
            logger.error(f"Error updating trade outcome: {str(e)}")
    
    async def analyze_performance(self, portfolio_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Analyze the performance of trading strategies
        
        Args:
            portfolio_id: Optional portfolio ID to filter analysis
            
        Returns:
            Dictionary with performance metrics
        """
        try:
            # Get all trade logs for analysis
            logs = await self._get_trade_logs(portfolio_id)
            if not logs:
                return {"error": "No trade logs found for analysis"}
                
            # Convert to DataFrame for easier analysis
            df = pd.DataFrame([log.dict() for log in logs])
            
            # Skip logs without outcomes
            df_completed = df[df["exit_price"].notna()]
            
            if len(df_completed) == 0:
                return {"error": "No completed trades found for analysis"}
                
            # Calculate win rates
            win_rate = len(df_completed[df_completed["profit_loss"] > 0]) / len(df_completed)
            
            # Calculate signal accuracy
            allora_accuracy = self._calculate_signal_accuracy(df_completed, "allora_signal")
            statistical_accuracy = self._calculate_signal_accuracy(df_completed, "statistical_signal")
            
            # Analyze by market condition
            market_condition_analysis = self._analyze_by_market_condition(df_completed)
            
            # Analyze by volatility
            volatility_analysis = self._analyze_by_volatility(df_completed)
            
            # Analyze manipulation detection effectiveness
            manipulation_analysis = self._analyze_manipulation_detection(df_completed)
            
            # Result summary
            return {
                "total_trades": len(df),
                "completed_trades": len(df_completed),
                "win_rate": win_rate,
                "avg_profit_loss_pct": df_completed["profit_loss_percent"].mean(),
                "max_profit_pct": df_completed["profit_loss_percent"].max(),
                "max_loss_pct": df_completed["profit_loss_percent"].min(),
                "allora_accuracy": allora_accuracy,
                "statistical_accuracy": statistical_accuracy,
                "market_condition": market_condition_analysis,
                "volatility": volatility_analysis,
                "manipulation": manipulation_analysis,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing performance: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_signal_accuracy(self, df: pd.DataFrame, signal_column: str) -> Dict[str, Any]:
        """Calculate accuracy of a signal type"""
        try:
            if signal_column not in df.columns:
                return {"error": f"Signal column {signal_column} not found"}
                
            accuracy = {
                "bullish": 0.0,
                "bearish": 0.0,
                "neutral": 0.0,
                "overall": 0.0
            }
            
            # Filter by signal type
            bullish = df[df[signal_column] == "bullish"]
            bearish = df[df[signal_column] == "bearish"]
            neutral = df[df[signal_column] == "neutral"]
            
            # Calculate accuracy for each signal
            if len(bullish) > 0:
                accuracy["bullish"] = len(bullish[bullish["profit_loss"] > 0]) / len(bullish)
                
            if len(bearish) > 0:
                accuracy["bearish"] = len(bearish[bearish["profit_loss"] > 0]) / len(bearish)
                
            if len(neutral) > 0:
                accuracy["neutral"] = len(neutral[neutral["profit_loss"] > 0]) / len(neutral)
                
            # Overall accuracy
            signal_correct = (
                (bullish["profit_loss"] > 0).sum() +
                (bearish["profit_loss"] > 0).sum() +
                (neutral["profit_loss"] > 0).sum()
            )
            accuracy["overall"] = signal_correct / len(df) if len(df) > 0 else 0.0
            
            # Add counts
            accuracy["bullish_count"] = len(bullish)
            accuracy["bearish_count"] = len(bearish)
            accuracy["neutral_count"] = len(neutral)
            
            return accuracy
            
        except Exception as e:
            logger.error(f"Error calculating signal accuracy: {str(e)}")
            return {"error": str(e)}
    
    def _analyze_by_market_condition(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze performance by market condition"""
        try:
            conditions = df["market_condition"].unique()
            result = {}
            
            for condition in conditions:
                condition_df = df[df["market_condition"] == condition]
                win_rate = len(condition_df[condition_df["profit_loss"] > 0]) / len(condition_df)
                avg_pnl = condition_df["profit_loss_percent"].mean()
                
                result[condition] = {
                    "count": len(condition_df),
                    "win_rate": win_rate,
                    "avg_profit_loss_pct": avg_pnl
                }
                
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing by market condition: {str(e)}")
            return {"error": str(e)}
    
    def _analyze_by_volatility(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze performance by volatility levels"""
        try:
            # Create volatility buckets
            df["volatility_bucket"] = pd.cut(
                df["volatility"],
                bins=[0, 0.2, 0.4, 0.6, 0.8, float("inf")],
                labels=["very_low", "low", "medium", "high", "very_high"]
            )
            
            result = {}
            for bucket in df["volatility_bucket"].unique():
                bucket_df = df[df["volatility_bucket"] == bucket]
                win_rate = len(bucket_df[bucket_df["profit_loss"] > 0]) / len(bucket_df)
                avg_pnl = bucket_df["profit_loss_percent"].mean()
                
                result[str(bucket)] = {
                    "count": len(bucket_df),
                    "win_rate": win_rate,
                    "avg_profit_loss_pct": avg_pnl
                }
                
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing by volatility: {str(e)}")
            return {"error": str(e)}
    
    def _analyze_manipulation_detection(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze effectiveness of manipulation detection"""
        try:
            # Split by manipulation detection
            manipulation_df = df[df["manipulation_detected"] == True]
            normal_df = df[df["manipulation_detected"] == False]
            
            # Calculate metrics
            manip_win_rate = len(manipulation_df[manipulation_df["profit_loss"] > 0]) / len(manipulation_df) if len(manipulation_df) > 0 else 0
            normal_win_rate = len(normal_df[normal_df["profit_loss"] > 0]) / len(normal_df) if len(normal_df) > 0 else 0
            
            return {
                "manipulation_detected_count": len(manipulation_df),
                "manipulation_win_rate": manip_win_rate,
                "normal_count": len(normal_df),
                "normal_win_rate": normal_win_rate,
                "effectiveness": (normal_win_rate - manip_win_rate) if len(manipulation_df) > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error analyzing manipulation detection: {str(e)}")
            return {"error": str(e)}
            
    async def generate_performance_report(self, days: int = 30) -> str:
        """
        Generate a human-readable performance report
        
        Args:
            days: Number of days to include in the report
            
        Returns:
            String with formatted performance report
        """
        try:
            # Get analysis data
            analysis = await self.analyze_performance()
            
            # Format the report
            report = f"""
            # Rebalancr Performance Report
            ## Period: Last {days} days
            Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            ## Overall Performance
            - Total Trades: {analysis.get('total_trades', 0)}
            - Completed Trades: {analysis.get('completed_trades', 0)}
            - Win Rate: {analysis.get('win_rate', 0) * 100:.2f}%
            - Average P/L: {analysis.get('avg_profit_loss_pct', 0) * 100:.2f}%
            - Max Profit: {analysis.get('max_profit_pct', 0) * 100:.2f}%
            - Max Loss: {analysis.get('max_loss_pct', 0) * 100:.2f}%
            
            ## Signal Accuracy
            ### Allora (Sentiment)
            - Overall: {analysis.get('allora_accuracy', {}).get('overall', 0) * 100:.2f}%
            - Bullish: {analysis.get('allora_accuracy', {}).get('bullish', 0) * 100:.2f}% ({analysis.get('allora_accuracy', {}).get('bullish_count', 0)} trades)
            - Bearish: {analysis.get('allora_accuracy', {}).get('bearish', 0) * 100:.2f}% ({analysis.get('allora_accuracy', {}).get('bearish_count', 0)} trades)
            
            ### Statistical
            - Overall: {analysis.get('statistical_accuracy', {}).get('overall', 0) * 100:.2f}%
            - Increase: {analysis.get('statistical_accuracy', {}).get('increase', 0) * 100:.2f}% ({analysis.get('statistical_accuracy', {}).get('increase_count', 0)} trades)
            - Decrease: {analysis.get('statistical_accuracy', {}).get('decrease', 0) * 100:.2f}% ({analysis.get('statistical_accuracy', {}).get('decrease_count', 0)} trades)
            
            ## Market Conditions Performance
            {self._format_market_condition_report(analysis.get('market_condition', {}))}
            
            ## Volatility Impact
            {self._format_volatility_report(analysis.get('volatility', {}))}
            
            ## Manipulation Detection
            - Manipulation Detected: {analysis.get('manipulation', {}).get('manipulation_detected_count', 0)} trades
            - Win Rate (Manipulation): {analysis.get('manipulation', {}).get('manipulation_win_rate', 0) * 100:.2f}%
            - Win Rate (Normal): {analysis.get('manipulation', {}).get('normal_win_rate', 0) * 100:.2f}%
            - Effectiveness: {analysis.get('manipulation', {}).get('effectiveness', 0) * 100:.2f}%
            
            ## Recommendations
            {self._generate_recommendations(analysis)}
            """
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating performance report: {str(e)}")
            return f"Error generating report: {str(e)}"
    
    def _format_market_condition_report(self, market_condition: Dict[str, Any]) -> str:
        """Format market condition section of the report"""
        if not market_condition or "error" in market_condition:
            return "No market condition data available."
            
        lines = []
        for condition, data in market_condition.items():
            lines.append(f"- {condition.capitalize()}: {data.get('win_rate', 0) * 100:.2f}% win rate, {data.get('avg_profit_loss_pct', 0) * 100:.2f}% avg P/L ({data.get('count', 0)} trades)")
            
        return "\n".join(lines)
    
    def _format_volatility_report(self, volatility: Dict[str, Any]) -> str:
        """Format volatility section of the report"""
        if not volatility or "error" in volatility:
            return "No volatility data available."
            
        lines = []
        for bucket, data in volatility.items():
            lines.append(f"- {bucket.replace('_', ' ').capitalize()}: {data.get('win_rate', 0) * 100:.2f}% win rate, {data.get('avg_profit_loss_pct', 0) * 100:.2f}% avg P/L ({data.get('count', 0)} trades)")
            
        return "\n".join(lines)
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> str:
        """Generate recommendations based on performance analysis"""
        recommendations = []
        
        # Check signal accuracy
        allora_accuracy = analysis.get('allora_accuracy', {}).get('overall', 0)
        stat_accuracy = analysis.get('statistical_accuracy', {}).get('overall', 0)
        
        if allora_accuracy > stat_accuracy:
            recommendations.append("- Consider increasing the weight of sentiment signals in the decision process")
        elif stat_accuracy > allora_accuracy:
            recommendations.append("- Consider increasing the weight of statistical signals in the decision process")
            
        # Check market conditions
        market_conditions = analysis.get('market_condition', {})
        best_condition = None
        best_win_rate = 0
        worst_condition = None
        worst_win_rate = 1
        
        for condition, data in market_conditions.items():
            if "error" in data:
                continue
                
            win_rate = data.get('win_rate', 0)
            if win_rate > best_win_rate:
                best_win_rate = win_rate
                best_condition = condition
                
            if win_rate < worst_win_rate:
                worst_win_rate = win_rate
                worst_condition = condition
                
        if best_condition:
            recommendations.append(f"- The strategy performs best in {best_condition} market conditions")
            
        if worst_condition:
            recommendations.append(f"- Consider avoiding trades during {worst_condition} market conditions")
            
        # Check volatility
        volatility = analysis.get('volatility', {})
        best_vol = None
        best_vol_win_rate = 0
        worst_vol = None
        worst_vol_win_rate = 1
        
        for bucket, data in volatility.items():
            if "error" in data:
                continue
                
            win_rate = data.get('win_rate', 0)
            if win_rate > best_vol_win_rate:
                best_vol_win_rate = win_rate
                best_vol = bucket
                
            if win_rate < worst_vol_win_rate:
                worst_vol_win_rate = win_rate
                worst_vol = bucket
                
        if best_vol:
            recommendations.append(f"- The strategy performs best with {best_vol.replace('_', ' ')} volatility")
            
        if worst_vol:
            recommendations.append(f"- Consider avoiding trades during {worst_vol.replace('_', ' ')} volatility periods")
            
        # Check manipulation detection
        manipulation = analysis.get('manipulation', {})
        effectiveness = manipulation.get('effectiveness', 0)
        
        if effectiveness > 0.1:  # 10% improvement
            recommendations.append("- Manipulation detection is effective, continue using it as a filter")
        elif effectiveness < 0:
            recommendations.append("- Manipulation detection may be filtering out good trades, consider recalibrating")
            
        if not recommendations:
            recommendations.append("- Not enough data for recommendations yet")
            
        return "\n".join(recommendations)
        
    async def _save_trade_log(self, log_entry: TradeLog) -> None:
        """Save trade log to database"""
        if self.db_manager:
            await self.db_manager.save_trade_log(log_entry.dict())
        else:
            logger.warning("No DB manager for saving trade log")
    
    async def _update_trade_log(self, log_entry: TradeLog) -> None:
        """Update trade log in database"""
        if self.db_manager:
            await self.db_manager.update_trade_log(log_entry.dict())
        else:
            logger.warning("No DB manager for updating trade log")
    
    async def _get_trade_log(self, log_id: int) -> Optional[TradeLog]:
        """Get trade log from database"""
        if self.db_manager:
            log_data = await self.db_manager.get_trade_log(log_id)
            if log_data:
                return TradeLog(**log_data)
        else:
            logger.warning("No DB manager for getting trade log")
        return None
    
    async def _get_trade_logs(self, portfolio_id: Optional[int] = None) -> List[TradeLog]:
        """Get trade logs from database"""
        if self.db_manager:
            filters = {"portfolio_id": portfolio_id} if portfolio_id else {}
            logs_data = await self.db_manager.get_trade_logs(filters)
            return [TradeLog(**log) for log in logs_data]
        else:
            logger.warning("No DB manager for getting trade logs")
            return [] 