# Topic model mappings
from typing import Dict, List, Optional, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field, validator

class AlloraPrediction(BaseModel):
    """Prediction result from Allora Network"""
    topic_id: int
    value: float
    timestamp: str
    previous_value: Optional[float] = None
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('value')
    def value_must_be_positive(cls, v):
        """Ensure prediction value is valid"""
        if v < 0 and not isinstance(v, bool):
            raise ValueError('Prediction value cannot be negative')
        return v

class SentimentAnalysis(BaseModel):
    """Sentiment analysis result"""
    asset: str
    sentiment: Literal["bullish", "bearish", "neutral"] = "neutral"
    fear_score: float = Field(ge=0.0, le=1.0)
    greed_score: float = Field(ge=0.0, le=1.0)
    primary_emotion: Literal["fear", "greed"] = "fear"
    manipulation_detected: bool = False
    manipulation_score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    timestamp: str
    
    @validator('fear_score', 'greed_score')
    def scores_must_be_valid(cls, v):
        if v < 0.0 or v > 1.0:
            raise ValueError('Score must be between 0 and 1')
        return v

class FearGreedIndex(BaseModel):
    """Fear/Greed index for a specific asset"""
    asset: str
    fear_greed_index: int = Field(ge=0, le=100)
    classification: Literal[
        "Extreme Fear", 
        "Fear", 
        "Neutral", 
        "Greed", 
        "Extreme Greed"
    ] = "Neutral"
    timestamp: str
    
    @validator('fear_greed_index')
    def index_must_be_valid(cls, v):
        if v < 0 or v > 100:
            raise ValueError('Index must be between 0 and 100')
        return v
        
    @validator('classification')
    def classification_must_match_index(cls, v, values):
        """Ensure classification matches the index value"""
        if 'fear_greed_index' in values:
            index = values['fear_greed_index']
            expected = "Neutral"
            
            if index < 25:
                expected = "Extreme Fear"
            elif index < 40:
                expected = "Fear"
            elif index < 60:
                expected = "Neutral"
            elif index < 80:
                expected = "Greed"
            else:
                expected = "Extreme Greed"
                
            if v != expected:
                raise ValueError(f'Classification should be {expected} for index {index}')
        return v

class MarketManipulation(BaseModel):
    """Market manipulation assessment"""
    asset: str
    manipulation_detected: bool = False
    manipulation_score: float = Field(ge=0.0, le=1.0)
    risk_level: Literal["Low", "Medium", "High"] = "Low"
    timestamp: str
    
    @validator('risk_level')
    def risk_level_must_match_score(cls, v, values):
        """Ensure risk level matches the manipulation score"""
        if 'manipulation_score' in values:
            score = values['manipulation_score']
            expected = "Low"
            
            if score > 0.8:
                expected = "High"
            elif score > 0.6:
                expected = "Medium"
                
            if v != expected:
                raise ValueError(f'Risk level should be {expected} for score {score}')
        return v

class AssetProfile(BaseModel):
    """Asset-specific profile for analysis"""
    symbol: str
    name: Optional[str] = None
    is_new_asset: bool = False  # Rose Heart advised caution with newer assets
    topic_keys: List[str] = []  # Relevant Allora topic keys
    sentiment_weight: float = Field(ge=0.0, le=1.0, default=0.25)
    statistical_weight: float = Field(ge=0.0, le=1.0, default=0.75)
    manipulation_threshold: float = Field(ge=0.0, le=1.0, default=0.6)
    
    @validator('sentiment_weight', 'statistical_weight')
    def weights_must_be_valid(cls, v):
        if v < 0.0 or v > 1.0:
            raise ValueError('Weight must be between 0 and 1')
        return v
        
    @validator('statistical_weight')
    def weights_must_sum_to_one(cls, v, values):
        """Ensure sentiment and statistical weights sum to 1.0"""
        if 'sentiment_weight' in values:
            sentiment_weight = values['sentiment_weight']
            if abs((sentiment_weight + v) - 1.0) > 0.01:
                raise ValueError('Sentiment and statistical weights must sum to 1.0')
        return v

class RebalanceSignal(BaseModel):
    """Signal for rebalancing a specific asset"""
    asset: str
    current_weight: float
    target_weight: float
    action: Literal["increase", "decrease", "maintain"] = "maintain"
    sentiment_signal: Optional[SentimentAnalysis] = None
    statistical_signal: Dict[str, Any] = {}
    combined_score: float = 0.0
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    @validator('target_weight')
    def weights_must_be_valid(cls, v):
        if v < 0.0 or v > 1.0:
            raise ValueError('Weight must be between 0 and 1')
        return v

class AssetAnalysisResult(BaseModel):
    """Complete analysis result for an asset"""
    asset: str
    sentiment: SentimentAnalysis
    fear_greed: FearGreedIndex
    manipulation: MarketManipulation
    statistical: Dict[str, Any]
    combined_score: float
    rebalance_signal: RebalanceSignal
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())