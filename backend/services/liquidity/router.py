"""FastAPI router for Liquidity Engine endpoints."""

from fastapi import APIRouter, HTTPException
from typing import Optional

from services.liquidity import build_liquidity_map
from services.liquidity.models import LiquidityRequest, LiquidityResponse

router = APIRouter(tags=["liquidity"])


@router.post("/map", response_model=LiquidityResponse)
async def get_liquidity_map(request: LiquidityRequest):
    """
    Build a full liquidity map for a given symbol and timeframe.

    Requires OHLCV data. For now returns a placeholder response.
    In production, fetches from exchange adapter cache.
    """
    try:
        # --- Placeholder: In production, fetch real OHLCV from exchange adapter ---
        # For now we return an empty map to validate the pipeline
        liquidity_map = build_liquidity_map(
            symbol=request.symbol,
            timeframe=request.timeframe,
            highs=[],
            lows=[],
            closes=[],
            opens=[],
            volumes=[],
        )
        return LiquidityResponse(success=True, data=liquidity_map, cached=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "liquidity-engine"}
