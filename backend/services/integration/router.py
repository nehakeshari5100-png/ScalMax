from fastapi import APIRouter, HTTPException
from services.integration.models import PipelineRequest, PipelineResponse
from services.integration.orchestrator import PipelineOrchestrator
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/run", response_model=PipelineResponse)
async def run_pipeline(request: PipelineRequest):
    """
    Run the full analysis pipeline end-to-end.

    Orchestrates all engines:
      Market Data → Indicators → Liquidity → Market Structure
      → Confluence → (Vision) → Decision → Signal

    Returns results from every stage including the final signal.
    """
    result = await PipelineOrchestrator.run(request)
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error or "Pipeline failed")
    return result


@router.post("/quick", response_model=PipelineResponse)
async def quick_analysis(request: PipelineRequest):
    """
    Run a quick analysis (no vision, no signal generation).

    Useful for fast market checks without committing to a signal.
    """
    request.include_vision = False
    request.auto_generate_signal = False
    result = await PipelineOrchestrator.run(request)
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error or "Pipeline failed")
    return result


@router.get("/health")
async def health():
    return {"status": "ok", "service": "integration"}
