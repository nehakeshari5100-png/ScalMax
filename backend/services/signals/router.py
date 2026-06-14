
"""FastAPI router for the Signal Engine and Signal Center."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from services.signals import (
    save_signal,
    get_signal,
    list_signals,
    update_signal,
    delete_signal,
    get_performance,
    SignalGenerator,
)
from services.signals.models import (
    SignalCreateRequest,
    SignalListResponse,
    SignalPerformance,
    SignalPerformanceResponse,
    SignalRecord,
    SignalResponse,
    SignalUpdateRequest,
)

router = APIRouter(tags=["signals"])


@router.post("/generate", response_model=SignalResponse)
async def generate_signal(request: SignalCreateRequest):
    """
    Generate a signal from decision parameters.

    Score below 70: No signal (No Trade).
    """
    try:
        signal = SignalGenerator.from_decision(
            symbol=request.symbol,
            timeframe=request.timeframe,
            direction=request.direction,
            confidence=request.confidence,
            confluence_score=request.confluence_score,
            entry=request.entry,
            stop_loss=request.stop_loss,
            take_profit_1=request.take_profit_1,
            take_profit_2=request.take_profit_2,
            reasoning=request.reasoning,
            reasons=request.reasons,
            risks=request.risks,
            strategy_version=request.strategy_version,
            session=request.session,
        )
        if signal is None:
            return SignalResponse(
                success=True,
                data=None,
                error="Score below threshold — no signal generated",
            )
        save_signal(signal)
        return SignalResponse(success=True, data=signal)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signals", response_model=SignalListResponse)
async def list_signal_history(
    symbol: Optional[str] = Query(None),
    timeframe: Optional[str] = Query(None),
    signal_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    direction: Optional[str] = Query(None),
    min_confidence: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1),
    page_size: int = Query(20),
):
    """List signals with filtering, search, and pagination."""
    try:
        signals, total = list_signals(
            symbol=symbol,
            timeframe=timeframe,
            signal_type=signal_type,
            status=status,
            direction=direction,
            min_confidence=min_confidence,
            search=search,
            page=page,
            page_size=min(page_size, 100),
        )
        return SignalListResponse(
            success=True,
            data=signals,
            total=total,
            page=page,
            page_size=page_size,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signals/{signal_id}", response_model=SignalResponse)
async def get_signal_by_id(signal_id: str):
    """Get a single signal by ID."""
    signal = get_signal(signal_id)
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    return SignalResponse(success=True, data=signal)


@router.patch("/signals/{signal_id}", response_model=SignalResponse)
async def update_signal_status(
    signal_id: str, request: SignalUpdateRequest
):
    """Update signal status, validation, or outcome."""
    updated = update_signal(
        signal_id=signal_id,
        status=request.status.value if request.status else None,
        validation_status=request.validation_status.value if request.validation_status else None,
        pnl=request.pnl,
        pnl_pct=request.pnl_pct,
        outcome=request.outcome,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Signal not found")
    signal = get_signal(signal_id)
    return SignalResponse(success=True, data=signal)


@router.delete("/signals/{signal_id}")
async def delete_signal_by_id(signal_id: str):
    """Delete a signal."""
    deleted = delete_signal(signal_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Signal not found")
    return {"success": True, "message": "Signal deleted"}


@router.get("/performance", response_model=SignalPerformanceResponse)
async def signal_performance(
    symbol: Optional[str] = Query(None),
    timeframe: Optional[str] = Query(None),
):
    """Get signal performance metrics."""
    try:
        perf = get_performance(symbol=symbol, timeframe=timeframe)
        return SignalPerformanceResponse(success=True, data=perf)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "signal-engine"}
