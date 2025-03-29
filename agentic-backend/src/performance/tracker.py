"""
Performance Tracker

Tracks and analyzes the performance of rebalancing strategies, both at the portfolio
level and for individual assets. Provides feedback for strategy improvement.
"""
import logging
import json
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class SignalType:
    ALLORA = "allora"
    STATISTICAL = "statistical"
    COMBINED = "combined"

class TradeRecord(BaseModel):
    """Record of a single trade or rebalance action"""
    id: str = Field(default_factory=lambda: f"trade_{datetime.now().timestamp()}")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    portfolio_id: Optional[int] = None
    user_id: Optional[str] = None
    asset: str
    action: str  # increase, decrease, maintain
    amount: float = 0.0
    price: float = 0.0
    value: float = 0.0
    
    # Signal data
    allora_signal: Optional[str] = None
    statistical_signal: Optional[str] = None
    combined_signal: Optional[str] = None
    confidence: float = 0.0
    
    # Market conditions
    market_condition: str = "normal"
    volatility: float = 0.0
    sentiment: Optional[str] = None
    manipulation_detected: bool = False
    
    # Execution data
    executed: bool = False
    tx_hash: Optional[str] = None
    execution_timestamp: Optional[str] = None
    
    # Results
    exit_price: Optional[float] = None
    exit_timestamp: Optional[str] = None
    profit_loss: Optional[float] = None
    profit_loss_percent: Optional[float] = None
    
    # Validation
    validated: bool = False
    validator_approval: bool = False
    validator_confidence: float = 0.0
    validator_reasoning: Optional[str] = None
    
class SignalAccuracy(BaseModel):
    """Accuracy metrics for a signal type"""
    total_signals: int = 0
    correct_signals: int = 0
    accuracy: float = 0.0
    profitable_trades: int = 0
    unprofitable_trades: int = 0
    avg_profit_percent: float = 0.0
    avg_loss_percent: float = 0.0
    by_market_condition: Dict[str, float] = Field(default_factory=dict)
    by_asset: Dict[str, float] = Field(default_factory=dict)

class PerformanceMetrics(BaseModel):
    """Overall performance metrics"""
    start_date: str = Field(default_factory=lambda: datetime.now().isoformat())
    end_date: str = Field(default_factory=lambda: datetime.now().isoformat())
    total_trades: int = 0
    profitable_trades: int = 0
    win_rate: float = 0.0
    avg_profit_percent: float = 0.0
    max_profit_percent: float = 0.0
    max_loss_percent: float = 0.0
    sharpe_ratio: Optional[float] = None
    volatility: Optional[float] = None
    allora_accuracy: Optional[SignalAccuracy] = None
    statistical_accuracy: Optional[SignalAccuracy] = None
    combined_accuracy: Optional[SignalAccuracy] = None
    
    # By market condition
    by_market_condition: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    # By asset
    by_asset: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    # Rebalancing effectiveness
    avg_rebalance_cost: float = 0.0
    avg_rebalance_benefit: float = 0.0
    avg_cost_benefit_ratio: float = 0.0

class PerformanceTracker:
    """
    Tracks and analyzes the performance of rebalancing strategies
    
    This tracker:
    1. Records all trades and rebalancing actions
    2. Analyzes the effectiveness of different signal types
    3. Calculates performance metrics
    4. Provides feedback for strategy improvement
    """
    
    def __init__(self, storage_path=None, db_manager=None):
        """Initialize tracker"""
        self.storage_path = storage_path or "performance_data"
        self.db_manager = db_manager
        
        # In-memory storage for trades
        self.trades: List[TradeRecord] = []
        
        # Load existing trades from storage if available
        self._load_trades()
    
    def record_trade(self, trade_data: Dict[str, Any]) -> str:
        """
        Record a trade or rebalancing action
        
        Args:
            trade_data: Dictionary with trade data
            
        Returns:
            Trade ID
        """
        # Create trade record
        trade = TradeRecord(**trade_data)
        
        # Add to in-memory storage
        self.trades.append(trade)
        
        # Save to persistent storage
        self._save_trade(trade)
        
        logger.info(f"Recorded trade: {trade.asset} {trade.action} for portfolio {trade.portfolio_id}")
        
        return trade.id
    
    def update_trade_outcome(self, trade_id: str, exit_price: float, exit_timestamp: Optional[str] = None) -> None:
        """
        Update trade outcome
        
        Args:
            trade_id: ID of the trade to update
            exit_price: Exit price
            exit_timestamp: Optional exit timestamp
        """
        # Find the trade
        for i, trade in enumerate(self.trades):
            if trade.id == trade_id:
                # Calculate profit/loss
                profit_loss = 0.0
                profit_loss_percent = 0.0
                
                if trade.action == "increase":
                    # Buy operation - profit if price increased
                    profit_loss = (exit_price - trade.price) * trade.amount
                    profit_loss_percent = (exit_price - trade.price) / trade.price if trade.price > 0 else 0
                elif trade.action == "decrease":
                    # Sell operation - profit if price decreased
                    profit_loss = (trade.price - exit_price) * trade.amount
                    profit_loss_percent = (trade.price - exit_price) / trade.price if trade.price > 0 else 0
                
                # Update trade record
                self.trades[i].exit_price = exit_price
                self.trades[i].exit_timestamp = exit_timestamp or datetime.now().isoformat()
                self.trades[i].profit_loss = profit_loss
                self.trades[i].profit_loss_percent = profit_loss_percent
                
                # Save to persistent storage
                self._save_trade(self.trades[i])
                
                logger.info(f"Updated trade outcome: {trade.asset} {trade.action} P/L: {profit_loss_percent:.2%}")
                
                break
    
    def record_rebalance(self, portfolio_id: int, trades: List[Dict[str, Any]], market_condition: str) -> List[str]:
        """
        Record a portfolio rebalance (multiple trades)
        
        Args:
            portfolio_id: Portfolio ID
            trades: List of trade dictionaries
            market_condition: Current market condition
            
        Returns:
            List of trade IDs
        """
        trade_ids = []
        
        for trade_data in trades:
            # Add portfolio and market data
            trade_data["portfolio_id"] = portfolio_id
            trade_data["market_condition"] = market_condition
            
            # Record the trade
            trade_id = self.record_trade(trade_data)
            trade_ids.append(trade_id)
        
        return trade_ids
    
    def calculate_signal_accuracy(self, signal_type: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> SignalAccuracy:
        """
        Calculate accuracy for a specific signal type
        
        Args:
            signal_type: Signal type (allora, statistical, combined)
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            
        Returns:
            SignalAccuracy object
        """
        # Filter trades by date if specified
        filtered_trades = self._filter_trades(start_date, end_date)
        
        # Filter trades with outcomes
        completed_trades = [t for t in filtered_trades if t.exit_price is not None]
        
        if not completed_trades:
            return SignalAccuracy()
        
        # Calculate accuracy metrics
        total_signals = 0
        correct_signals = 0
        profitable_trades = 0
        unprofitable_trades = 0
        profit_sum = 0.0
        loss_sum = 0.0
        
        # Track by market condition and asset
        by_market_condition: Dict[str, Dict[str, int]] = {}
        by_asset: Dict[str, Dict[str, int]] = {}
        
        for trade in completed_trades:
            signal_value = None
            
            if signal_type == SignalType.ALLORA:
                signal_value = trade.allora_signal
            elif signal_type == SignalType.STATISTICAL:
                signal_value = trade.statistical_signal
            else:  # Combined
                signal_value = trade.combined_signal
            
            if not signal_value:
                continue
                
            total_signals += 1
            
            # Check if trade was profitable
            is_profitable = trade.profit_loss is not None and trade.profit_loss > 0
            
            # Check if signal was correct
            is_correct = False
            
            if signal_value == "bullish" and trade.action == "increase" and is_profitable:
                is_correct = True
            elif signal_value == "bearish" and trade.action == "decrease" and is_profitable:
                is_correct = True
            elif signal_value == "neutral" and trade.action == "maintain":
                is_correct = True
                
            if is_correct:
                correct_signals += 1
                
            if is_profitable:
                profitable_trades += 1
                profit_sum += trade.profit_loss_percent or 0
            else:
                unprofitable_trades += 1
                loss_sum += trade.profit_loss_percent or 0
                
            # Update market condition stats
            market_condition = trade.market_condition
            if market_condition not in by_market_condition:
                by_market_condition[market_condition] = {"total": 0, "correct": 0}
                
            by_market_condition[market_condition]["total"] += 1
            if is_correct:
                by_market_condition[market_condition]["correct"] += 1
                
            # Update asset stats
            asset = trade.asset
            if asset not in by_asset:
                by_asset[asset] = {"total": 0, "correct": 0}
                
            by_asset[asset]["total"] += 1
            if is_correct:
                by_asset[asset]["correct"] += 1
        
        # Calculate final metrics
        accuracy = correct_signals / total_signals if total_signals > 0 else 0
        avg_profit = profit_sum / profitable_trades if profitable_trades > 0 else 0
        avg_loss = loss_sum / unprofitable_trades if unprofitable_trades > 0 else 0
        
        # Calculate accuracy by market condition
        condition_accuracy = {}
        for condition, stats in by_market_condition.items():
            condition_accuracy[condition] = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
            
        # Calculate accuracy by asset
        asset_accuracy = {}
        for asset, stats in by_asset.items():
            asset_accuracy[asset] = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
            
        return SignalAccuracy(
            total_signals=total_signals,
            correct_signals=correct_signals,
            accuracy=accuracy,
            profitable_trades=profitable_trades,
            unprofitable_trades=unprofitable_trades,
            avg_profit_percent=avg_profit,
            avg_loss_percent=avg_loss,
            by_market_condition=condition_accuracy,
            by_asset=asset_accuracy
        )
    
    def calculate_performance_metrics(self, portfolio_id: Optional[int] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> PerformanceMetrics:
        """
        Calculate overall performance metrics
        
        Args:
            portfolio_id: Optional portfolio ID for filtering
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            
        Returns:
            PerformanceMetrics object
        """
        # Filter trades
        trades = self._filter_trades(start_date, end_date, portfolio_id)
        
        # Filter trades with outcomes
        completed_trades = [t for t in trades if t.exit_price is not None]
        
        if not completed_trades:
            return PerformanceMetrics(
                start_date=start_date or datetime.now().isoformat(),
                end_date=end_date or datetime.now().isoformat()
            )
            
        # Calculate basic metrics
        total_trades = len(completed_trades)
        profitable_trades = sum(1 for t in completed_trades if t.profit_loss is not None and t.profit_loss > 0)
        win_rate = profitable_trades / total_trades if total_trades > 0 else 0
        
        profit_percentages = [t.profit_loss_percent for t in completed_trades if t.profit_loss_percent is not None]
        avg_profit_percent = sum(profit_percentages) / len(profit_percentages) if profit_percentages else 0
        max_profit_percent = max(profit_percentages) if profit_percentages else 0
        max_loss_percent = min(profit_percentages) if profit_percentages else 0
        
        # Calculate signal accuracies
        allora_accuracy = self.calculate_signal_accuracy(SignalType.ALLORA, start_date, end_date)
        statistical_accuracy = self.calculate_signal_accuracy(SignalType.STATISTICAL, start_date, end_date)
        combined_accuracy = self.calculate_signal_accuracy(SignalType.COMBINED, start_date, end_date)
        
        # Calculate metrics by market condition
        by_market_condition = {}
        for condition in set(t.market_condition for t in completed_trades):
            condition_trades = [t for t in completed_trades if t.market_condition == condition]
            condition_profitable = sum(1 for t in condition_trades if t.profit_loss is not None and t.profit_loss > 0)
            condition_win_rate = condition_profitable / len(condition_trades) if condition_trades else 0
            
            condition_pnl = [t.profit_loss_percent for t in condition_trades if t.profit_loss_percent is not None]
            condition_avg_pnl = sum(condition_pnl) / len(condition_pnl) if condition_pnl else 0
            
            by_market_condition[condition] = {
                "total_trades": len(condition_trades),
                "win_rate": condition_win_rate,
                "avg_profit_percent": condition_avg_pnl
            }
            
        # Calculate metrics by asset
        by_asset = {}
        for asset in set(t.asset for t in completed_trades):
            asset_trades = [t for t in completed_trades if t.asset == asset]
            asset_profitable = sum(1 for t in asset_trades if t.profit_loss is not None and t.profit_loss > 0)
            asset_win_rate = asset_profitable / len(asset_trades) if asset_trades else 0
            
            asset_pnl = [t.profit_loss_percent for t in asset_trades if t.profit_loss_percent is not None]
            asset_avg_pnl = sum(asset_pnl) / len(asset_pnl) if asset_pnl else 0
            
            by_asset[asset] = {
                "total_trades": len(asset_trades),
                "win_rate": asset_win_rate,
                "avg_profit_percent": asset_avg_pnl
            }
            
        # Calculate rebalancing effectiveness
        portfolio_rebalances = self._get_portfolio_rebalances(portfolio_id, start_date, end_date)
        avg_rebalance_cost = 0.0
        avg_rebalance_benefit = 0.0
        avg_cost_benefit_ratio = 0.0
        
        if portfolio_rebalances:
            costs = [r.get("cost", 0) for r in portfolio_rebalances]
            benefits = [r.get("benefit", 0) for r in portfolio_rebalances]
            
            avg_rebalance_cost = sum(costs) / len(costs) if costs else 0
            avg_rebalance_benefit = sum(benefits) / len(benefits) if benefits else 0
            
            ratios = [b/c for b, c in zip(benefits, costs) if c > 0]
            avg_cost_benefit_ratio = sum(ratios) / len(ratios) if ratios else 0
        
        # Calculate volatility and Sharpe ratio if sufficient data
        volatility = None
        sharpe_ratio = None
        
        if len(profit_percentages) >= 10:
            volatility = np.std(profit_percentages) * np.sqrt(252)  # Annualized
            avg_return = sum(profit_percentages) / len(profit_percentages)
            risk_free_rate = 0.01  # 1% assumed risk-free rate
            sharpe_ratio = (avg_return - risk_free_rate) / volatility if volatility > 0 else 0
        
        return PerformanceMetrics(
            start_date=start_date or min(t.timestamp for t in completed_trades),
            end_date=end_date or max(t.timestamp for t in completed_trades),
            total_trades=total_trades,
            profitable_trades=profitable_trades,
            win_rate=win_rate,
            avg_profit_percent=avg_profit_percent,
            max_profit_percent=max_profit_percent,
            max_loss_percent=max_loss_percent,
            sharpe_ratio=sharpe_ratio,
            volatility=volatility,
            allora_accuracy=allora_accuracy,
            statistical_accuracy=statistical_accuracy,
            combined_accuracy=combined_accuracy,
            by_market_condition=by_market_condition,
            by_asset=by_asset,
            avg_rebalance_cost=avg_rebalance_cost,
            avg_rebalance_benefit=avg_rebalance_benefit,
            avg_cost_benefit_ratio=avg_cost_benefit_ratio
        )
    
    def get_recommendations(self, metrics: Optional[PerformanceMetrics] = None) -> List[str]:
        """
        Generate strategic recommendations based on performance metrics
        
        Args:
            metrics: Optional performance metrics (will be calculated if not provided)
            
        Returns:
            List of recommendation strings
        """
        if metrics is None:
            metrics = self.calculate_performance_metrics()
            
        recommendations = []
        
        # Check win rate
        if metrics.win_rate < 0.5:
            recommendations.append("Overall win rate is below 50%. Consider reviewing your rebalancing strategy.")
        
        # Compare signal accuracies
        if metrics.allora_accuracy and metrics.statistical_accuracy:
            allora_acc = metrics.allora_accuracy.accuracy
            statistical_acc = metrics.statistical_accuracy.accuracy
            
            if allora_acc > statistical_acc + 0.1:  # Allora is 10% more accurate
                recommendations.append("Allora signals are significantly more accurate than statistical signals. Consider increasing the weight of sentiment analysis.")
            elif statistical_acc > allora_acc + 0.1:  # Statistical is 10% more accurate
                recommendations.append("Statistical signals are significantly more accurate than Allora signals. Consider increasing the weight of statistical analysis.")
        
        # Check market conditions
        if metrics.by_market_condition:
            best_condition = max(metrics.by_market_condition.items(), key=lambda x: x[1]["win_rate"])
            worst_condition = min(metrics.by_market_condition.items(), key=lambda x: x[1]["win_rate"])
            
            recommendations.append(f"Strategy performs best in {best_condition[0]} market conditions ({best_condition[1]['win_rate']:.2%} win rate).")
            recommendations.append(f"Strategy performs worst in {worst_condition[0]} market conditions ({worst_condition[1]['win_rate']:.2%} win rate). Consider adjusting or disabling rebalancing during these conditions.")
        
        # Check asset performance
        if metrics.by_asset:
            best_asset = max(metrics.by_asset.items(), key=lambda x: x[1]["win_rate"])
            worst_asset = min(metrics.by_asset.items(), key=lambda x: x[1]["win_rate"])
            
            recommendations.append(f"Strategy performs best with {best_asset[0]} ({best_asset[1]['win_rate']:.2%} win rate).")
            recommendations.append(f"Strategy performs worst with {worst_asset[0]} ({worst_asset[1]['win_rate']:.2%} win rate). Consider reviewing asset-specific parameters.")
        
        # Check rebalancing effectiveness
        if metrics.avg_cost_benefit_ratio < 2.0:
            recommendations.append(f"Average cost-benefit ratio ({metrics.avg_cost_benefit_ratio:.2f}) is below the recommended 2.0. Consider increasing the minimum threshold for rebalancing.")
        
        return recommendations
    
    def generate_report(self, portfolio_id: Optional[int] = None, days: int = 30) -> str:
        """
        Generate a performance report
        
        Args:
            portfolio_id: Optional portfolio ID for filtering
            days: Number of days to include in the report
            
        Returns:
            Formatted report string
        """
        # Calculate date range
        end_date = datetime.now().isoformat()
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Calculate metrics
        metrics = self.calculate_performance_metrics(portfolio_id, start_date, end_date)
        
        # Generate recommendations
        recommendations = self.get_recommendations(metrics)
        
        # Format the report
        report = f"""
        # Performance Report
        
        ## Overview
        
        Period: Last {days} days ({start_date} to {end_date})
        Total Trades: {metrics.total_trades}
        Win Rate: {metrics.win_rate:.2%}
        Average P/L: {metrics.avg_profit_percent:.2%}
        
        ## Signal Performance
        
        | Signal Type | Accuracy | Win Rate | Avg Profit | Avg Loss |
        |-------------|----------|----------|------------|----------|
        | Allora | {metrics.allora_accuracy.accuracy if metrics.allora_accuracy else 'N/A':.2%} | {metrics.allora_accuracy.profitable_trades / metrics.allora_accuracy.total_signals if metrics.allora_accuracy and metrics.allora_accuracy.total_signals > 0 else 'N/A'} | {metrics.allora_accuracy.avg_profit_percent if metrics.allora_accuracy else 'N/A':.2%} | {metrics.allora_accuracy.avg_loss_percent if metrics.allora_accuracy else 'N/A':.2%} |
        | Statistical | {metrics.statistical_accuracy.accuracy if metrics.statistical_accuracy else 'N/A':.2%} | {metrics.statistical_accuracy.profitable_trades / metrics.statistical_accuracy.total_signals if metrics.statistical_accuracy and metrics.statistical_accuracy.total_signals > 0 else 'N/A'} | {metrics.statistical_accuracy.avg_profit_percent if metrics.statistical_accuracy else 'N/A':.2%} | {metrics.statistical_accuracy.avg_loss_percent if metrics.statistical_accuracy else 'N/A':.2%} |
        | Combined | {metrics.combined_accuracy.accuracy if metrics.combined_accuracy else 'N/A':.2%} | {metrics.combined_accuracy.profitable_trades / metrics.combined_accuracy.total_signals if metrics.combined_accuracy and metrics.combined_accuracy.total_signals > 0 else 'N/A'} | {metrics.combined_accuracy.avg_profit_percent if metrics.combined_accuracy else 'N/A':.2%} | {metrics.combined_accuracy.avg_loss_percent if metrics.combined_accuracy else 'N/A':.2%} |
        
        ## Market Conditions
        
        """
        
        # Add market condition table
        if metrics.by_market_condition:
            for condition, stats in metrics.by_market_condition.items():
                report += f"{condition}: {stats['total_trades']} trades, {stats['win_rate']:.2%} win rate, {stats['avg_profit_percent']:.2%} avg P/L\n        "
        
        report += """
        
        ## Asset Performance
        
        """
        
        # Add asset performance table
        if metrics.by_asset:
            for asset, stats in metrics.by_asset.items():
                report += f"{asset}: {stats['total_trades']} trades, {stats['win_rate']:.2%} win rate, {stats['avg_profit_percent']:.2%} avg P/L\n        "
        
        report += """
        
        ## Rebalancing Effectiveness
        
        Average Cost: {metrics.avg_rebalance_cost:.2f}
        Average Benefit: {metrics.avg_rebalance_benefit:.2f}
        Average Cost-Benefit Ratio: {metrics.avg_cost_benefit_ratio:.2f}
        
        ## Recommendations
        
        """
        
        # Add recommendations
        for recommendation in recommendations:
            report += f"- {recommendation}\n        "
        
        return report
    
    def _filter_trades(self, start_date: Optional[str] = None, end_date: Optional[str] = None, portfolio_id: Optional[int] = None) -> List[TradeRecord]:
        """Filter trades by date and portfolio"""
        filtered = self.trades
        
        if start_date:
            filtered = [t for t in filtered if t.timestamp >= start_date]
            
        if end_date:
            filtered = [t for t in filtered if t.timestamp <= end_date]
            
        if portfolio_id is not None:
            filtered = [t for t in filtered if t.portfolio_id == portfolio_id]
            
        return filtered
    
    def _get_portfolio_rebalances(self, portfolio_id: Optional[int] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get portfolio rebalance data for analysis"""
        # In a real implementation, this would query the database
        # For hackathon, return dummy data
        return [
            {"date": "2023-08-01", "cost": 10, "benefit": 25},
            {"date": "2023-08-07", "cost": 12, "benefit": 18},
            {"date": "2023-08-14", "cost": 8, "benefit": 20}
        ]
    
    def _save_trade(self, trade: TradeRecord) -> None:
        """Save trade to persistent storage"""
        if self.db_manager:
            # Save to database
            self.db_manager.save_trade(trade.dict())
        else:
            # Save to file
            self._ensure_storage_path()
            file_path = os.path.join(self.storage_path, f"{trade.id}.json")
            
            with open(file_path, "w") as f:
                json.dump(trade.dict(), f, indent=2)
    
    def _load_trades(self) -> None:
        """Load trades from persistent storage"""
        if self.db_manager:
            # Load from database
            trade_dicts = self.db_manager.get_all_trades()
            self.trades = [TradeRecord(**t) for t in trade_dicts]
        else:
            # Load from files
            self._ensure_storage_path()
            
            if not os.path.exists(self.storage_path):
                return
                
            for file_name in os.listdir(self.storage_path):
                if file_name.endswith(".json"):
                    file_path = os.path.join(self.storage_path, file_name)
                    
                    try:
                        with open(file_path, "r") as f:
                            trade_dict = json.load(f)
                            self.trades.append(TradeRecord(**trade_dict))
                    except Exception as e:
                        logger.error(f"Error loading trade from {file_path}: {e}")
    
    def _ensure_storage_path(self) -> None:
        """Ensure storage path exists"""
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)
            
# Singleton instance
_instance = None

def get_performance_tracker() -> PerformanceTracker:
    """Get or create the singleton instance"""
    global _instance
    if _instance is None:
        _instance = PerformanceTracker()
    return _instance
