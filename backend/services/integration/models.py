from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from enum import Enum


class PipelineStage(str, Enum):
    FETCH_CANDLES = "fetch_candles"
    CALCULATE_INDICATORS = "calculate_indicators"
    DETECT_LIQUIDITY = "detect_liquidity"
    ANALYZE_STRUCTURE = "analyze_structure"
    SCORE_CONFLUENCE = "score_confluence"
    ANALYZE_VISION = "analyze_vision"
    MAKE_DECISION = "make_decision"
    GENERATE_SIGNAL = "generate_signal"


class PipelineRequest(BaseModel):
    symbol: str = "BTCUSDT"
    timeframe: str = "5m"
    exchange: str = "binance"
    lookback: int = 200
    include_vision: bool = False
    vision_model: str = "google/gemma-3-vision"
    api_key: Optional[str] = None
    chart_image_base64: Optional[str] = None
    auto_generate_signal: bool = True


class PipelineResult(BaseModel):
    stage: PipelineStage
    status: str = "pending"
    duration_ms: float = 0.0
    data: Optional[Any] = None
    error: Optional[str] = None


class PipelineResponse(BaseModel):
    success: bool
    execution_id: str
    total_duration_ms: float = 0.0
    stages: List[PipelineResult] = Field(default_factory=list)
    symbol: str = ""
    timeframe: str = ""
    exchange: str = ""
    decision: Optional[Any] = None
    signal: Optional[Any] = None
    error: Optional[str] = None
