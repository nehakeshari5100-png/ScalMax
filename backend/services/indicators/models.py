from pydantic import BaseModel, Field
from typing import List, Optional


class EMAResult(BaseModel):
    ema9: float = 0.0
    ema20: float = 0.0
    ema50: float = 0.0
    ema200: float = 0.0


class MACDResult(BaseModel):
    macd_line: float = 0.0
    signal_line: float = 0.0
    histogram: float = 0.0


class RSIData(BaseModel):
    rsi: float = 0.0
    oversold: bool = False
    overbought: bool = False


class StochRSIData(BaseModel):
    k: float = 0.0
    d: float = 0.0
    oversold: bool = False
    overbought: bool = False


class VWAPResult(BaseModel):
    vwap: float = 0.0
    price_above_vwap: Optional[bool] = None


class ATRResult(BaseModel):
    atr: float = 0.0
    atr_percent: float = 0.0


class BollingerBandsResult(BaseModel):
    upper: float = 0.0
    middle: float = 0.0
    lower: float = 0.0
    bandwidth: float = 0.0
    percent_b: float = 0.0


class TrendStrengthResult(BaseModel):
    score: float = 0.0
    direction: str = "neutral"
    description: str = ""


class MomentumStrengthResult(BaseModel):
    score: float = 0.0
    direction: str = "neutral"
    description: str = ""


class VolatilityResult(BaseModel):
    score: float = 0.0
    description: str = ""


class VolumeSpikeResult(BaseModel):
    is_spike: bool = False
    ratio: float = 0.0
    direction: str = "neutral"


class IndicatorSet(BaseModel):
    """Complete set of all calculated indicators for a symbol/timeframe."""
    symbol: str = ""
    timeframe: str = ""
    timestamp: int = 0

    # Trend
    ema9: float = 0.0
    ema20: float = 0.0
    ema50: float = 0.0
    ema200: float = 0.0

    # Momentum
    rsi: float = 0.0
    macd: MACDResult = Field(default_factory=MACDResult)
    stoch_rsi: StochRSIData = Field(default_factory=StochRSIData)

    # Volume
    vwap: float = 0.0
    volume_delta: float = 0.0
    volume_spike: VolumeSpikeResult = Field(default_factory=VolumeSpikeResult)

    # Volatility
    atr: float = 0.0
    atr_percent: float = 0.0
    bollinger: BollingerBandsResult = Field(default_factory=BollingerBandsResult)

    # Composite Scores
    trend_score: float = 0.0
    momentum_score: float = 0.0
    volatility_score: float = 0.0

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BTCUSDT",
                "timeframe": "5m",
                "timestamp": 1700000000000,
                "ema9": 67542.50,
                "ema20": 67489.00,
                "ema50": 67300.00,
                "ema200": 67000.00,
                "rsi": 62.5,
                "macd": {"macd_line": 45.2, "signal_line": 38.1, "histogram": 7.1},
                "vwap": 67450.00,
                "atr": 125.50,
                "trend_score": 0.75,
                "momentum_score": 0.62,
                "volatility_score": 0.35,
            }
        }


class IndicatorRequest(BaseModel):
    symbol: str
    timeframe: str
    exchange: str = "binance"
    lookback: int = 500


class IndicatorResponse(BaseModel):
    success: bool
    data: Optional[IndicatorSet] = None
    error: Optional[str] = None
    cached: bool = False
