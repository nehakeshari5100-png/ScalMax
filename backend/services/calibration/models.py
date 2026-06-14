from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class TradeOutcome(str, Enum):
    WIN = "win"
    LOSS = "loss"
    BREAK_EVEN = "break_even"


class BucketLabel(str, Enum):
    BUCKET_90_100 = "90-100"
    BUCKET_80_89 = "80-89"
    BUCKET_70_79 = "70-79"
    BUCKET_60_69 = "60-69"
    BUCKET_BELOW_60 = "below_60"


# Bucket definitions: (label, min_score, max_score)
BUCKET_DEFS = [
    (BucketLabel.BUCKET_90_100, 90, 100),
    (BucketLabel.BUCKET_80_89, 80, 89),
    (BucketLabel.BUCKET_70_79, 70, 79),
    (BucketLabel.BUCKET_60_69, 60, 69),
    (BucketLabel.BUCKET_BELOW_60, 0, 59),
]


def bucket_for_score(score: int) -> BucketLabel:
    """Return the bucket label for a given raw score."""
    for label, lo, hi in BUCKET_DEFS:
        if lo <= score <= hi:
            return label
    return BucketLabel.BUCKET_BELOW_60


class BucketStats(BaseModel):
    """Historical performance stats for a single score bucket."""
    label: str = ""
    min_score: int = 0
    max_score: int = 0
    trade_count: int = 0
    wins: int = 0
    losses: int = 0
    break_even: int = 0
    win_rate: float = 0.0
    loss_rate: float = 0.0
    total_return: float = 0.0
    total_fees: float = 0.0
    avg_return: float = 0.0
    profit_factor: float = 0.0
    expected_return: float = 0.0
    # Blended estimate for small samples
    adjusted_win_rate: float = 0.0
    adjusted_confidence: float = 0.0


class TradeRecord(BaseModel):
    """A single recorded trade outcome for calibration."""
    trade_id: str = ""
    symbol: str = ""
    raw_score: int = Field(default=0, ge=0, le=100)
    outcome: TradeOutcome = TradeOutcome.BREAK_EVEN
    profit_loss: float = 0.0
    fees: float = 0.0
    timestamp: int = 0
    direction: str = "neutral"
    bucket: str = ""


class CalibrationData(BaseModel):
    """Complete calibration dataset."""
    buckets: List[BucketStats] = Field(default_factory=list)
    total_trades: int = 0
    overall_win_rate: float = 0.0
    last_updated: int = 0
    min_samples_required: int = 10

    def bucket_for(self, label: str) -> Optional[BucketStats]:
        for b in self.buckets:
            if b.label == label:
                return b
        return None


class CalibrationResult(BaseModel):
    """Calibrated output for a single score."""
    raw_score: int = 0
    calibrated_score: int = 0
    bucket_label: str = ""
    bucket_win_rate: float = 0.0
    sample_size: int = 0
    has_sufficient_data: bool = False
    calibrated_confidence: int = 0


class CalibrateRequest(BaseModel):
    """Request to calibrate a list of scores."""
    scores: List[int] = Field(default_factory=list)


class RecordTradeRequest(BaseModel):
    """Request to record a trade outcome."""
    symbol: str = ""
    raw_score: int = Field(default=0, ge=0, le=100)
    outcome: TradeOutcome = TradeOutcome.BREAK_EVEN
    profit_loss: float = 0.0
    fees: float = 0.0
    direction: str = "neutral"


class CalibrateResponse(BaseModel):
    success: bool
    data: Optional[List[CalibrationResult]] = None
    error: Optional[str] = None


class CalibrationStatsResponse(BaseModel):
    success: bool
    data: Optional[CalibrationData] = None
    error: Optional[str] = None
