"""
Trade Reviewer Service

This module provides a second opinion on trade decisions,
implementing the multi-layered architecture from the Allora HyperLiquid AutoTradeBot example.
"""
import json
import logging
import asyncio
from typing import Dict, Any, Optional, List
import aiohttp
from pydantic import BaseModel, Field
from datetime import datetime

logger = logging.getLogger(__name__)

class ReviewRequest(BaseModel):
    """Request for trade review"""
    asset: str
    current_price: float
    predicted_price: Optional[float] = None
    prediction_diff_pct: Optional[float] = None
    direction: str  # "increase", "decrease", "maintain"
    market_condition: str  # "normal", "volatile", "bear", "bull"
    sentiment: Optional[str] = None
    volatility: Optional[float] = None
    manipulation_risk: Optional[float] = None
    below_median_frequency: Optional[float] = None
    
class ReviewResult(BaseModel):
    """Result of trade review"""
    asset: str
    approval: bool = False
    confidence: float = Field(ge=0.0, le=100.0)
    reasoning: str = ""
    risk_score: int = Field(ge=1, le=10)
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class TradeReviewer:
    """
    AI-based trade validator that provides a second opinion on trades/rebalancing.
    
    Implements the multi-layered decision architecture recommended by Rose Heart,
    similar to the DeepSeek reviewer in the Allora HyperLiquid AutoTradeBot.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.use_external_ai = self.config.get("USE_EXTERNAL_AI", False)
        self.api_key = self.config.get("REVIEWER_API_KEY", "")
        self.api_url = self.config.get("REVIEWER_API_URL", "")
        
    async def review_trade(self, trade_data: Dict[str, Any]) -> ReviewResult:
        """
        Review a potential trade or rebalancing action
        
        Args:
            trade_data: Dictionary with trade data
            
        Returns:
            ReviewResult with approval and reasoning
        """
        try:
            # Convert to ReviewRequest for validation
            request = ReviewRequest(
                asset=trade_data.get("asset", ""),
                current_price=trade_data.get("current_price", 0),
                predicted_price=trade_data.get("predicted_price"),
                prediction_diff_pct=trade_data.get("prediction_diff_pct"),
                direction=trade_data.get("direction", "maintain"),
                market_condition=trade_data.get("market_condition", "normal"),
                sentiment=trade_data.get("sentiment"),
                volatility=trade_data.get("volatility"),
                manipulation_risk=trade_data.get("manipulation_risk"),
                below_median_frequency=trade_data.get("below_median_frequency")
            )
            
            # Use external AI if configured
            if self.use_external_ai and self.api_key and self.api_url:
                return await self._external_review(request)
            else:
                # Otherwise use rule-based review
                return await self._rule_based_review(request)
                
        except Exception as e:
            logger.error(f"Review failed: {str(e)}")
            return ReviewResult(
                asset=trade_data.get("asset", "unknown"),
                approval=False,
                confidence=0.0,
                reasoning=f"Review failed: {str(e)}",
                risk_score=10  # Maximum risk on failure
            )
    
    async def _external_review(self, request: ReviewRequest) -> ReviewResult:
        """Use external AI service for review"""
        prompt = self._create_review_prompt(request)
        
        async with aiohttp.ClientSession() as session:
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "model": "claude-3",  # Use Claude 3 or GPT-4
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3
                }
                
                async with session.post(self.api_url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                        return self._parse_analysis(content, request.asset)
                    else:
                        error = await response.text()
                        raise Exception(f"API error: {error}")
            except Exception as e:
                logger.error(f"External review failed: {str(e)}")
                # Fall back to rule-based review
                return await self._rule_based_review(request)
    
    def _create_review_prompt(self, request: ReviewRequest) -> str:
        """Create prompt for AI review"""
        return f"""
        As an AI trading expert, review this potential trade:
        
        Asset: {request.asset}
        Current Price: ${request.current_price:,.2f}
        {"Predicted Price: $" + str(request.predicted_price) if request.predicted_price else ""}
        {"Prediction Difference: " + str(request.prediction_diff_pct) + "%" if request.prediction_diff_pct else ""}
        Direction: {request.direction}
        Market Condition: {request.market_condition}
        {"Sentiment: " + request.sentiment if request.sentiment else ""}
        {"Volatility: " + str(request.volatility) if request.volatility else ""}
        {"Manipulation Risk: " + str(request.manipulation_risk) if request.manipulation_risk else ""}
        {"Below Median Frequency: " + str(request.below_median_frequency) if request.below_median_frequency else ""}
        
        Please analyze this trade based on Rose Heart's trading principles:
        1. Use sentiment for emotional analysis
        2. Use statistics for numerical decisions
        3. Beware of high volatility
        4. Pay attention to market manipulation
        5. Consider if benefits outweigh costs
        
        Respond in JSON format with:
        1. approval (true/false)
        2. confidence (0-100)
        3. reasoning (string)
        4. risk_score (1-10)
        """
    
    def _parse_analysis(self, analysis: str, asset: str) -> ReviewResult:
        """Parse AI response into ReviewResult"""
        try:
            # Find JSON block in the response
            start = analysis.find('{')
            end = analysis.rfind('}')
            
            # Ensure valid JSON bounds
            if start == -1 or end == -1:
                raise ValueError("No valid JSON found in the response")
                
            json_str = analysis[start:end + 1]  # Extract JSON substring
            result_dict = json.loads(json_str)
            
            # Convert to ReviewResult
            return ReviewResult(
                asset=asset,
                approval=result_dict.get("approval", False),
                confidence=float(result_dict.get("confidence", 0.0)),
                reasoning=result_dict.get("reasoning", ""),
                risk_score=int(result_dict.get("risk_score", 10))
            )
        except Exception as e:
            logger.error(f"Failed to parse AI response: {str(e)}")
            return ReviewResult(
                asset=asset,
                approval=False,
                confidence=0.0,
                reasoning=f"Failed to parse AI response: {str(e)}",
                risk_score=10
            )
    
    async def _rule_based_review(self, request: ReviewRequest) -> ReviewResult:
        """
        Rule-based review for trades
        
        This implements Rose Heart's rules:
        - Be cautious with high volatility assets
        - Be wary of market manipulation
        - Don't trade frequently due to fees
        """
        approval = True
        confidence = 60.0  # Default moderate confidence
        risk_score = 5     # Default moderate risk
        reasons = []
        
        # 1. Check market condition
        if request.market_condition == "volatile":
            approval = False
            confidence = 80.0
            risk_score = 8
            reasons.append("Market is too volatile for rebalancing")
        
        # 2. Check manipulation risk
        if request.manipulation_risk and request.manipulation_risk > 0.6:
            approval = False
            confidence = 90.0
            risk_score = 9
            reasons.append(f"High manipulation risk detected ({request.manipulation_risk:.2f})")
        
        # 3. Check direction against sentiment
        if request.direction == "increase" and request.sentiment == "fear":
            approval = False
            confidence = 70.0
            risk_score = 7
            reasons.append("Increasing position during fear sentiment is risky")
        
        # 4. Check direction against below median frequency
        if request.direction == "increase" and request.below_median_frequency and request.below_median_frequency > 0.6:
            approval = False
            confidence = 75.0
            risk_score = 6
            reasons.append("Asset frequently trades below median - avoid increasing position")
        
        # 5. Special case for stablecoins
        if request.asset in ["USDC", "USDT", "DAI"] and request.direction == "decrease":
            approval = False
            confidence = 85.0
            risk_score = 7
            reasons.append("Maintaining stablecoin reserves is recommended for safety")
        
        # Build reasoning string
        reasoning = "Trade approved." if approval else "Trade rejected: " + "; ".join(reasons)
        
        return ReviewResult(
            asset=request.asset,
            approval=approval,
            confidence=confidence,
            reasoning=reasoning,
            risk_score=risk_score
        )
        
    async def bulk_review(self, trades: List[Dict[str, Any]]) -> List[ReviewResult]:
        """Review multiple trades in parallel"""
        tasks = [self.review_trade(trade) for trade in trades]
        return await asyncio.gather(*tasks)
        
    async def validate_rebalance_plan(
        self, 
        assets: List[Dict[str, Any]], 
        market_condition: str
    ) -> Dict[str, Any]:
        """
        Validate a complete rebalancing plan
        
        Args:
            assets: List of assets with rebalancing actions
            market_condition: Current market condition
            
        Returns:
            Dictionary with validation results
        """
        # Prepare trades for review
        trades = []
        for asset in assets:
            trades.append({
                "asset": asset.get("asset", ""),
                "current_price": asset.get("current_price", 0),
                "direction": asset.get("action", "maintain"),
                "market_condition": market_condition,
                "sentiment": asset.get("sentiment", {}).get("primary_emotion", "neutral"),
                "volatility": asset.get("statistical", {}).get("volatility"),
                "manipulation_risk": asset.get("manipulation", {}).get("manipulation_score", 0),
                "below_median_frequency": asset.get("statistical", {}).get("below_median_frequency")
            })
        
        # Review each trade
        results = await self.bulk_review(trades)
        
        # Calculate overall approval
        num_assets = len(assets)
        num_approved = sum(1 for r in results if r.approval)
        
        # Calculate weighted risk score
        overall_risk = sum(r.risk_score for r in results) / len(results) if results else 10
        
        return {
            "approved": num_approved == num_assets,
            "approval_rate": num_approved / num_assets if num_assets > 0 else 0,
            "overall_risk": overall_risk,
            "results": [r.dict() for r in results],
            "timestamp": datetime.now().isoformat()
        } 