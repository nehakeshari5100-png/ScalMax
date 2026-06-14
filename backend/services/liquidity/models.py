from pydantic import BaseModel, Field
from typing import List, Optional


class LiquidityLevel(BaseModel):
    price: float = 0.0
    strength: int = Field(default=1, ge=1, le=10, description="Confidence 1-10")
    touches: int = 0
    type: str = ""  # 'support' | 'resistance'
    direction: str = ""  # 'buy' | 'sell'


class EqualHighLow(BaseModel):
    price: float = 0.0
    count: int = 0
    strength: int = Field(default=1, ge=1, le=10)
    type: str = ""  # 'equal_high' | 'equal_low'
    timestamps: List[int] = Field(default_factory=list)


class FVG(BaseModel):
    direction: str = ""  # 'bullish' | 'bearish'
    gap_high: float = 0.0
    gap_low: float = 0.0
    gap_size: float = 0.0
    start_index: int = 0
    end_index: int = 0
    strength: int = Field(default=1, ge=1, le=10)
    mitigated: bool = False
    mitigation_price: Optional[float] = None


class OrderBlock(BaseModel):
    direction: str = ""  # 'bullish' | 'bearish'
    start_price: float = 0.0
    end_price: float = 0.0
    start_index: int = 0
    strength: int = Field(default=1, ge=1, le=10)
    mitigated: bool = False
    mitigation_index: Optional[int] = None
    type: str = "order_block"  # 'order_block' | 'breaker'


class LiquiditySweep(BaseModel):
    direction: str = ""  # 'buy' | 'sell'
    price: float = 0.0
    wick_size: float = 0.0
    volume_ratio: float = 0.0
    reversal_strength: int = Field(default=1, ge=1, le=10)
    timestamp: int = 0
    type: str = ""  # 'sweep' | 'stop_hunt'


class Imbalance(BaseModel):
    direction: str = ""  # 'bullish' | 'bearish'
    high: float = 0.0
    low: float = 0.0
    size: float = 0.0
    strength: int = Field(default=1, ge=1, le=10)


class LiquidityMap(BaseModel):
    symbol: str = ""
    timeframe: str = ""
    timestamp: int = 0

    # Core structures
    bullish_liquidity: List[LiquidityLevel] = Field(default_factory=list)
    bearish_liquidity: List[LiquidityLevel] = Field(default_factory=list)
    equal_highs: List[EqualHighLow] = Field(default_factory=list)
    equal_lows: List[EqualHighLow] = Field(default_factory=list)
    fvg: List[FVG] = Field(default_factory=list)
    order_blocks: List[OrderBlock] = Field(default_factory=list)
    breaker_blocks: List[OrderBlock] = Field(default_factory=list)
    liquidity_sweeps: List[LiquiditySweep] = Field(default_factory=list)
    imbalances: List[Imbalance] = Field(default_factory=list)

    # Aggregate metrics
    overall_confidence: int = Field(default=50, ge=0, le=100)
    bullish_volume: float = 0.0
    bearish_volume: float = 0.0

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BTCUSDT",
                "timeframe": "5m",
                "bullish_liquidity": [{"price": 67100, "strength": 8, "touches": 3}],
                "bearish_liquidity": [{"price": 68200, "strength": 7, "touches": 2}],
                "equal_highs": [{"price": 68050, "count": 3, "strength": 8}],
                "fvg": [{"direction": "bullish", "gap_high": 67350, "gap_low": 67280}],
            }
        }


class LiquidityRequest(BaseModel):
    symbol: str
    timeframe: str = "5m"
    exchange: str = "binance"
    lookback: int = 200


class LiquidityResponse(BaseModel):
    success: bool
    data: Optional[LiquidityMap] = None
    error: Optional[str] = None
    cached: bool = False
