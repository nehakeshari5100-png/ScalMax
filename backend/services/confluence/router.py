
"""FastAPI router for Confluence Scoring Engine."""

from fastapi import APIRouter, HTTPException

from services.confluence import score_confluence
from services.confluence.models import ScoreRequest, ScoreResponse

router = APIRouter(tags=["confluence"])


@router.post("/score", response_model=ScoreResponse)
async def get_confluence_score(request: ScoreRequest):
    """
    Compute a confluence score from indicator, market structure,
    and liquidity engine inputs.
    """
    try:
        output = score_confluence(request.data)
        return ScoreResponse(success=True, data=output, cached=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "confluence-engine"}
