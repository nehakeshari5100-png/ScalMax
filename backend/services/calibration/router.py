
"""FastAPI router for the Confidence Calibration Engine."""

from fastapi import APIRouter, HTTPException

from services.calibration import calibrate_many, record_trade, get_calibration_data, store
from services.calibration.models import (
    CalibrateRequest,
    CalibrateResponse,
    RecordTradeRequest,
    CalibrationStatsResponse,
)

router = APIRouter(tags=["calibration"])


@router.post("/calibrate", response_model=CalibrateResponse)
async def calibrate_scores(request: CalibrateRequest):
    """
    Calibrate raw confluence scores based on historical outcomes.

    Returns calibrated confidence for each score bucket.
    """
    try:
        results = calibrate_many(request.scores)
        return CalibrateResponse(success=True, data=results, error=None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/record", response_model=CalibrateResponse)
async def record_trade_outcome(request: RecordTradeRequest):
    """
    Record a trade outcome to improve future calibration.
    """
    try:
        record_trade(
            symbol=request.symbol,
            raw_score=request.raw_score,
            outcome=request.outcome.value,
            profit_loss=request.profit_loss,
            fees=request.fees,
            direction=request.direction,
        )
        # Re-calibrate this score and return
        results = calibrate_many([request.raw_score])
        return CalibrateResponse(success=True, data=results, error=None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=CalibrationStatsResponse)
async def get_calibration_stats(min_samples: int = 10):
    """
    Get calibration statistics for all score buckets.
    """
    try:
        data = get_calibration_data(min_samples)
        return CalibrationStatsResponse(success=True, data=data, error=None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear")
async def clear_calibration_data():
    """Clear all recorded trade outcomes (for testing)."""
    store.clear_records()
    return {"success": True, "message": "Calibration data cleared"}


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "calibration-engine"}
