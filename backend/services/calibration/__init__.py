
"""
Confidence Calibration Engine.

Tracks historical trade outcomes grouped by score buckets
(90-100, 80-89, 70-79, 60-69, below_60), computes win rate,
expected return, and profit factor per bucket, and adjusts
confidence estimates to be evidence-based.

Usage:
    from services.calibration import calibrate, record_trade

    # Record outcome
    record_trade(symbol="BTCUSDT", raw_score=87, outcome="win")

    # Calibrate a score
    result = calibrate(87)  # Returns CalibrateResponse
"""

from services.calibration.store import CalibrationStore
from services.calibration.models import (
    CalibrateRequest,
    CalibrateResponse,
    CalibrationResult,
    CalibrationData,
    RecordTradeRequest,
    TradeOutcome,
    TradeRecord,
    bucket_for_score,
)

store = CalibrationStore.get_instance()


def calibrate(raw_score: int) -> CalibrationResult:
    """Calibrate a single raw confluence score."""
    return store.calibrate_scores([raw_score])[0]


def calibrate_many(scores: list[int], min_samples: int = 10) -> list[CalibrationResult]:
    """Calibrate multiple scores at once."""
    return store.calibrate_scores(scores, min_samples)


def record_trade(
    symbol: str,
    raw_score: int,
    outcome: str,
    profit_loss: float = 0.0,
    fees: float = 0.0,
    direction: str = "neutral",
) -> None:
    """Record a trade outcome for future calibration."""
    from services.calibration.models import TradeOutcome

    record = TradeRecord(
        symbol=symbol,
        raw_score=raw_score,
        outcome=TradeOutcome(outcome),
        profit_loss=profit_loss,
        fees=fees,
        direction=direction,
        bucket=bucket_for_score(raw_score).value,
    )
    store.record_trade(record)


def get_calibration_data(min_samples: int = 10) -> CalibrationData:
    """Get full calibration stats across all buckets."""
    return store.compute_calibration(min_samples)


__all__ = [
    "calibrate",
    "calibrate_many",
    "record_trade",
    "get_calibration_data",
    "store",
]
