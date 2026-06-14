
"""FastAPI router for the Backtesting Engine."""

import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from services.backtesting.engine import (
    run_backtest,
    get_result,
    list_results,
    delete_result,
)
from services.backtesting.models import (
    BacktestRunRequest,
    BacktestRunResponse,
    BacktestListResponse,
)

router = APIRouter(tags=["backtesting"])


@router.post("/run", response_model=BacktestRunResponse)
async def run_backtest_endpoint(request: BacktestRunRequest):
    """Run a full backtest with the given configuration."""
    try:
        result = run_backtest(request)
        return BacktestRunResponse(success=True, data=result, error=result.error)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results", response_model=BacktestListResponse)
async def list_backtest_results(
    symbol: str = "",
    timeframe: str = "",
    strategy_version: str = "",
    limit: int = 20,
    offset: int = 0,
):
    """List past backtest results with optional filters."""
    try:
        results, total = list_results(
            symbol=symbol or None,
            timeframe=timeframe or None,
            strategy_version=strategy_version or None,
            limit=limit,
            offset=offset,
        )
        return BacktestListResponse(success=True, data=results, total=total)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results/{rid}", response_model=BacktestRunResponse)
async def get_backtest_result(rid: str):
    """Get a single backtest result by ID."""
    result = get_result(rid)
    if not result:
        raise HTTPException(status_code=404, detail="Backtest result not found")
    return BacktestRunResponse(success=True, data=result)


@router.delete("/results/{rid}")
async def delete_backtest_result(rid: str):
    """Delete a backtest result."""
    deleted = delete_result(rid)
    if not deleted:
        raise HTTPException(status_code=404, detail="Backtest result not found")
    return {"success": True, "message": "Backtest result deleted"}


@router.get("/report/{rid}")
async def get_backtest_report(rid: str):
    """Download the BACKTEST_REPORT.md for a completed backtest."""
    result = get_result(rid)
    if not result or not result.report_path:
        raise HTTPException(status_code=404, detail="Report not found")
    if not os.path.exists(result.report_path):
        raise HTTPException(status_code=404, detail="Report file not found")
    return FileResponse(
        result.report_path,
        media_type="text/markdown",
        filename=f"BACKTEST_REPORT_{result.config.symbol}_{result.config.strategy_version}.md",
    )


@router.get("/supported")
async def get_supported_options():
    from services.backtesting.models import SUPPORTED_ASSETS, SUPPORTED_TIMEFRAMES
    return {
        "assets": SUPPORTED_ASSETS,
        "timeframes": SUPPORTED_TIMEFRAMES,
    }


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "backtesting-engine"}
