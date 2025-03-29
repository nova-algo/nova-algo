# Implementation for rebalancr/backend/rebalancr/testing/forward_tester.py

"""
Forward Testing Framework

Implements Rose Heart's recommendation to use forward testing
instead of just backtesting, to account for market chaos,
manipulation, and unpredictability.
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from rebalancr.intelligence.intelligence_engine import IntelligenceEngine
from rebalancr.strategy.engine import StrategyEngine
from rebalancr.performance.analyzer import PerformanceAnalyzer

logger = logging.getLogger(__name__)

class ForwardTester:
    """
    Runs parallel simulations without executing trades.
    Records predictions and compares to actual outcomes.
    Refines weights based on performance.
    """
    
    def __init__(
        self,
        intelligence_engine: IntelligenceEngine,
        strategy_engine: StrategyEngine,
        performance_analyzer: PerformanceAnalyzer,
        db_manager,
        config: Dict[str, Any]
    ):
        self.intelligence_engine = intelligence_engine
        self.strategy_engine = strategy_engine
        self.performance_analyzer = performance_analyzer
        self.db_manager = db_manager
        self.config = config
        
        # Storage for predictions and outcomes
        self.predictions = {}
        self.outcomes = {}
        self.test_runs = {}
        self.weight_history = {}
        
        # Default weight configuration
        self.default_weights = {
            "sentiment": 0.25,
            "below_median": 0.25,
            "volatility": 0.25,
            "trend": 0.25
        }
    
    async def start_test_run(
        self, 
        user_id: str, 
        portfolio_id: int,
        run_name: str,
        duration_days: int = 30,
        check_interval_hours: int = 24
    ) -> Dict[str, Any]:
        """Begin a new forward test run"""
        try:
            # Get portfolio data
            portfolio = await self.db_manager.get_portfolio(portfolio_id)
            
            # Create a new test run
            run_id = f"{run_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            self.test_runs[run_id] = {
                "user_id": user_id,
                "portfolio_id": portfolio_id,
                "run_name": run_name,
                "start_time": datetime.now().isoformat(),
                "end_time": (datetime.now() + timedelta(days=duration_days)).isoformat(),
                "check_interval_hours": check_interval_hours,
                "status": "running",
                "predictions": [],
                "outcomes": [],
                "portfolio_snapshot": portfolio,
                "current_weights": self.intelligence_engine.weights.copy()
            }
            
            # Save weight starting point
            self.weight_history[run_id] = [
                {
                    "timestamp": datetime.now().isoformat(),
                    "weights": self.intelligence_engine.weights.copy()
                }
            ]
            
            # Make initial prediction
            initial_prediction = await self._make_prediction(user_id, portfolio_id, run_id)
            
            return {
                "run_id": run_id,
                "status": "started",
                "end_date": self.test_runs[run_id]["end_time"],
                "initial_prediction": initial_prediction
            }
        except Exception as e:
            logger.error(f"Error starting test run: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Error starting test run"
            }
    
    async def record_prediction(
        self, 
        run_id: str,
        prediction: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Store a prediction for later evaluation"""
        try:
            if run_id not in self.test_runs:
                raise ValueError(f"Test run {run_id} not found")
                
            # Add timestamp if not present
            if "timestamp" not in prediction:
                prediction["timestamp"] = datetime.now().isoformat()
                
            # Add to predictions list
            self.test_runs[run_id]["predictions"].append(prediction)
            
            return {
                "run_id": run_id,
                "prediction_id": len(self.test_runs[run_id]["predictions"]) - 1,
                "timestamp": prediction["timestamp"],
                "status": "recorded"
            }
        except Exception as e:
            logger.error(f"Error recording prediction: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Error recording prediction"
            }
    
    async def record_outcome(
        self,
        run_id: str,
        prediction_id: int,
        outcome: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Record actual outcome for a previous prediction"""
        try:
            if run_id not in self.test_runs:
                raise ValueError(f"Test run {run_id} not found")
                
            if prediction_id >= len(self.test_runs[run_id]["predictions"]):
                raise ValueError(f"Prediction ID {prediction_id} not found")
                
            # Add timestamp if not present
            if "timestamp" not in outcome:
                outcome["timestamp"] = datetime.now().isoformat()
                
            # Link to the prediction
            outcome["prediction_id"] = prediction_id
            
            # Add to outcomes list
            self.test_runs[run_id]["outcomes"].append(outcome)
            
            # Optimize weights based on this outcome
            await self._optimize_weights(run_id, prediction_id, outcome)
            
            return {
                "run_id": run_id,
                "prediction_id": prediction_id,
                "outcome_id": len(self.test_runs[run_id]["outcomes"]) - 1,
                "timestamp": outcome["timestamp"],
                "status": "recorded"
            }
        except Exception as e:
            logger.error(f"Error recording outcome: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Error recording outcome"
            }
    
    async def compare_outcomes(self, run_id: str) -> Dict[str, Any]:
        """Compare predictions to actual results"""
        try:
            if run_id not in self.test_runs:
                raise ValueError(f"Test run {run_id} not found")
                
            test_run = self.test_runs[run_id]
            
            # Map outcomes to predictions
            prediction_outcome_pairs = []
            
            for outcome in test_run["outcomes"]:
                prediction_id = outcome.get("prediction_id")
                if prediction_id is not None and prediction_id < len(test_run["predictions"]):
                    prediction = test_run["predictions"][prediction_id]
                    
                    # Calculate accuracy metrics
                    accuracy = self._calculate_accuracy(prediction, outcome)
                    
                    prediction_outcome_pairs.append({
                        "prediction": prediction,
                        "outcome": outcome,
                        "accuracy": accuracy
                    })
            
            # Calculate overall statistics
            overall_stats = self._calculate_overall_stats(prediction_outcome_pairs)
            
            # Calculate weight effectiveness
            weight_effectiveness = self._analyze_weight_effectiveness(run_id)
            
            return {
                "run_id": run_id,
                "pairs_analyzed": len(prediction_outcome_pairs),
                "overall_stats": overall_stats,
                "weight_effectiveness": weight_effectiveness,
                "weight_history": self.weight_history.get(run_id, []),
                "detailed_pairs": prediction_outcome_pairs
            }
        except Exception as e:
            logger.error(f"Error comparing outcomes: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Error comparing outcomes"
            }
    
    async def optimize_weights(self, run_id: str) -> Dict[str, Any]:
        """Update weights based on performance"""
        try:
            if run_id not in self.test_runs:
                raise ValueError(f"Test run {run_id} not found")
                
            # Get comparison data
            comparison = await self.compare_outcomes(run_id)
            
            # Get current weights
            current_weights = self.test_runs[run_id].get("current_weights", self.default_weights)
            
            # Calculate optimal weights
            optimal_weights = {}
            
            # Get signal accuracies from comparison
            signal_accuracies = comparison.get("overall_stats", {}).get("signal_accuracies", {})
            
            if signal_accuracies:
                # Calculate total accuracy
                total_accuracy = sum(signal_accuracies.values())
                
                # If all signals are inaccurate, reset to default
                if total_accuracy <= 0:
                    optimal_weights = self.default_weights.copy()
                else:
                    # Set weights proportional to accuracy
                    for signal, accuracy in signal_accuracies.items():
                        if signal in current_weights:
                            optimal_weights[signal] = max(0.1, accuracy / total_accuracy)
                    
                    # Normalize weights to sum to 1.0
                    weight_sum = sum(optimal_weights.values())
                    if weight_sum > 0:
                        optimal_weights = {k: v / weight_sum for k, v in optimal_weights.items()}
            else:
                # If no accuracy data, use current weights
                optimal_weights = current_weights.copy()
            
            # Update weights in the test run
            self.test_runs[run_id]["current_weights"] = optimal_weights
            
            # Add to weight history
            self.weight_history.setdefault(run_id, []).append({
                "timestamp": datetime.now().isoformat(),
                "weights": optimal_weights
            })
            
            # Optionally update the real Intelligence Engine weights
            # This would only be done after significant testing
            # self.intelligence_engine.weights = optimal_weights
            
            return {
                "run_id": run_id,
                "previous_weights": current_weights,
                "new_weights": optimal_weights,
                "signal_accuracies": signal_accuracies
            }
        except Exception as e:
            logger.error(f"Error optimizing weights: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Error optimizing weights"
            }
    
    async def get_test_run_status(self, run_id: str) -> Dict[str, Any]:
        """Get the status of a test run"""
        try:
            if run_id not in self.test_runs:
                raise ValueError(f"Test run {run_id} not found")
                
            test_run = self.test_runs[run_id]
            
            return {
                "run_id": run_id,
                "run_name": test_run["run_name"],
                "status": test_run["status"],
                "start_time": test_run["start_time"],
                "end_time": test_run["end_time"],
                "predictions_count": len(test_run["predictions"]),
                "outcomes_count": len(test_run["outcomes"]),
                "current_weights": test_run["current_weights"]
            }
        except Exception as e:
            logger.error(f"Error getting test run status: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Error getting test run status"
            }
    
    async def _make_prediction(
        self, 
        user_id: str, 
        portfolio_id: int,
        run_id: str
    ) -> Dict[str, Any]:
        """Generate a prediction using the Intelligence Engine"""
        # Get recommendation from Intelligence Engine
        recommendation = await self.intelligence_engine.analyze_portfolio(
            user_id=user_id,
            portfolio_id=portfolio_id
        )
        
        # Extract prediction
        prediction = {
            "timestamp": datetime.now().isoformat(),
            "portfolio_id": portfolio_id,
            "rebalance_recommended": recommendation.get("rebalance_recommended", False),
            "target_allocations": recommendation.get("target_allocations", {}),
            "sentiment_analysis": recommendation.get("sentiment_analysis", {}),
            "fear_greed_index": recommendation.get("fear_greed_index", {}),
            "manipulation_detected": recommendation.get("manipulation_detected", False),
            "weights_used": self.test_runs[run_id]["current_weights"]
        }
        
        # Record the prediction
        await self.record_prediction(run_id, prediction)
        
        return prediction
    
    async def _optimize_weights(
        self,
        run_id: str,
        prediction_id: int,
        outcome: Dict[str, Any]
    ) -> None:
        """Update weights based on the accuracy of a prediction"""
        # Only optimize weights periodically, not on every outcome
        if len(self.test_runs[run_id]["outcomes"]) % 5 == 0:
            await self.optimize_weights(run_id)
    
    def _calculate_accuracy(
        self,
        prediction: Dict[str, Any],
        outcome: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate accuracy metrics for a prediction-outcome pair"""
        # Initialize accuracy metrics
        accuracy = {
            "overall": 0.0,
            "by_asset": {},
            "by_signal": {
                "sentiment": 0.0,
                "below_median": 0.0,
                "volatility": 0.0,
                "trend": 0.0
            }
        }
        
        # Calculate overall prediction accuracy
        if "rebalance_recommended" in prediction and "actual_benefit" in outcome:
            # If rebalance was recommended and beneficial, that's accurate
            # If rebalance was not recommended and would not have been beneficial, that's accurate
            rebalance_accurate = (
                (prediction["rebalance_recommended"] and outcome["actual_benefit"] > 0) or
                (not prediction["rebalance_recommended"] and outcome["actual_benefit"] <= 0)
            )
            accuracy["overall"] = 1.0 if rebalance_accurate else 0.0
        
        # Calculate asset-specific accuracy
        predicted_allocations = prediction.get("target_allocations", {})
        actual_prices = outcome.get("actual_prices", {})
        
        for asset, allocation in predicted_allocations.items():
            if asset in actual_prices:
                # If allocation increased and price increased, that's accurate
                # If allocation decreased and price decreased, that's accurate
                initial_price = actual_prices[asset].get("initial_price", 0)
                final_price = actual_prices[asset].get("final_price", 0)
                
                if initial_price > 0 and final_price > 0:
                    price_change = (final_price - initial_price) / initial_price
                    
                    # Get original allocation from portfolio snapshot
                    original_allocation = 0
                    if "portfolio_snapshot" in outcome:
                        for asset_data in outcome["portfolio_snapshot"].get("assets", []):
                            if asset_data["symbol"] == asset:
                                original_allocation = asset_data["percentage"] / 100
                                break
                    
                    allocation_change = allocation - original_allocation
                    
                    # If signs match, prediction was accurate
                    if (allocation_change > 0 and price_change > 0) or (allocation_change < 0 and price_change < 0):
                        accuracy["by_asset"][asset] = 1.0
                    else:
                        accuracy["by_asset"][asset] = 0.0
        
        # Calculate signal-specific accuracy
        if "by_signal_accuracy" in outcome:
            accuracy["by_signal"] = outcome["by_signal_accuracy"]
        
        return accuracy
    
    def _calculate_overall_stats(
        self,
        pairs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate overall statistics from prediction-outcome pairs"""
        if not pairs:
            return {"overall_accuracy": 0.0}
            
        # Calculate overall accuracy
        overall_accuracy = sum(p["accuracy"]["overall"] for p in pairs) / len(pairs)
        
        # Calculate accuracy by asset
        assets = set()
        for pair in pairs:
            assets.update(pair["accuracy"].get("by_asset", {}).keys())
        
        asset_accuracies = {}
        for asset in assets:
            asset_pairs = [p for p in pairs if asset in p["accuracy"].get("by_asset", {})]
            if asset_pairs:
                asset_accuracies[asset] = sum(p["accuracy"]["by_asset"][asset] for p in asset_pairs) / len(asset_pairs)
        
        # Calculate accuracy by signal
        signals = ["sentiment", "below_median", "volatility", "trend"]
        signal_accuracies = {}
        
        for signal in signals:
            signal_pairs = [p for p in pairs if signal in p["accuracy"].get("by_signal", {})]
            if signal_pairs:
                signal_accuracies[signal] = sum(p["accuracy"]["by_signal"][signal] for p in signal_pairs) / len(signal_pairs)
        
        return {
            "overall_accuracy": overall_accuracy,
            "asset_accuracies": asset_accuracies,
            "signal_accuracies": signal_accuracies,
            "sample_size": len(pairs)
        }
    
    def _analyze_weight_effectiveness(self, run_id: str) -> Dict[str, Any]:
        """Analyze how effective different weight configurations have been"""
        weight_history = self.weight_history.get(run_id, [])
        if len(weight_history) <= 1:
            return {"insufficient_data": True}
            
        # Get all pairs from this run
        test_run = self.test_runs[run_id]
        
        # Map predictions to weights
        weight_effectiveness = {}
        
        for weight_point in weight_history:
            timestamp = datetime.fromisoformat(weight_point["timestamp"])
            weights = weight_point["weights"]
            weight_key = json.dumps(weights)
            
            # Find predictions made with these weights
            matching_pairs = []
            
            for outcome in test_run["outcomes"]:
                prediction_id = outcome.get("prediction_id")
                if prediction_id is not None and prediction_id < len(test_run["predictions"]):
                    prediction = test_run["predictions"][prediction_id]
                    prediction_timestamp = datetime.fromisoformat(prediction["timestamp"])
                    
                    # If prediction was made after this weight point but before the next one
                    if prediction_timestamp >= timestamp:
                        # Check if prediction used these weights
                        if prediction.get("weights_used") == weights:
                            # Calculate accuracy
                            accuracy = self._calculate_accuracy(prediction, outcome)
                            matching_pairs.append({
                                "prediction": prediction,
                                "outcome": outcome,
                                "accuracy": accuracy
                            })
            
            # Calculate effectiveness for this weight configuration
            if matching_pairs:
                overall_stats = self._calculate_overall_stats(matching_pairs)
                
                weight_effectiveness[weight_key] = {
                    "weights": weights,
                    "timestamp": weight_point["timestamp"],
                    "pairs_count": len(matching_pairs),
                    "overall_accuracy": overall_stats["overall_accuracy"],
                    "signal_accuracies": overall_stats.get("signal_accuracies", {})
                }
        
        return {
            "configurations_analyzed": len(weight_effectiveness),
            "by_configuration": weight_effectiveness
        }