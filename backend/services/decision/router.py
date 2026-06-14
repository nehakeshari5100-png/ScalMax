
"""FastAPI router for the Master AI Decision Engine."""

from typing import Optional
from fastapi import APIRouter, HTTPException

from services.decision import MasterDecisionEngine
from services.decision.models import DecisionInput, DecisionOutput, DecisionResponse

router = APIRouter(tags=["decision"])


@router.post("/decide", response_model=DecisionResponse)
async def make_decision(request: DecisionInput):
    """
    Master decision endpoint.

    Combines all deterministic engines with optional Gemma Vision analysis
    to produce a single trading decision.

    If deterministic analysis and vision analysis disagree, returns NO TRADE
    with reason "Analysis Conflict".
    """
    try:
        output = MasterDecisionEngine.decide(request)
        return DecisionResponse(success=True, data=output, error=None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "master-decision-engine"}
