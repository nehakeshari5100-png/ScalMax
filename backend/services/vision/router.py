"""FastAPI router for the Vision Analysis Engine with scoring orchestration."""

from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from services.vision.analyzer import VisionAnalyzer
from services.vision.scoring import score_observation
from services.vision.models import VisionAnalysisResponse

router = APIRouter(tags=["vision"])

ALLOWED_FORMATS = {"png", "jpeg", "jpg", "gif", "webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024


@router.post("/analyze", response_model=VisionAnalysisResponse)
async def analyze_chart(
    file: UploadFile = File(...),
    api_key: str = Form(...),
    model: str = Form("openrouter/free"),
    prompt: str = Form(""),
):
    """
    Upload a chart screenshot.
    Flow: analyze → extract observations → score → return trade decision.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    image_data = await file.read()
    if len(image_data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // 1024 // 1024}MB",
        )

    img_format = _detect_image_format(image_data)
    if img_format is None:
        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if ext in ("png", "jpg", "jpeg", "gif", "webp"):
            img_format = ext
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format. Supported: {', '.join(ALLOWED_FORMATS)}",
            )
    if img_format not in ALLOWED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image format: {img_format}. Supported: {', '.join(ALLOWED_FORMATS)}",
        )

    # Step 1: Extract observations from AI
    analysis_result = await VisionAnalyzer.analyze(
        api_key=api_key,
        image_data=image_data,
        model=model,
        prompt=prompt,
    )

    if not analysis_result.success or analysis_result.observation is None:
        return analysis_result

    # Step 2: Score observations → trade decision
    trade = score_observation(analysis_result.observation)

    # Return combined response
    return VisionAnalysisResponse(
        success=True,
        trade=trade,
        observation=analysis_result.observation,
        raw=analysis_result.raw,
        model=analysis_result.model,
    )


@router.get("/models")
async def list_vision_models():
    return {
        "models": [
            {
                "id": "openrouter/free",
                "name": "OpenRouter Free Router",
                "description": "Auto-routes to best free vision model — $0 cost",
                "default": True,
                "free": True,
            },
            {
                "id": "google/gemma-3-12b-it:free",
                "name": "Gemma 3 12B (free)",
                "description": "Free fast vision model",
                "default": False,
                "free": True,
            },
            {
                "id": "google/gemma-3-4b-it:free",
                "name": "Gemma 3 4B (free)",
                "description": "Smallest free vision model — fastest",
                "default": False,
                "free": True,
            },
            {
                "id": "nvidia/nemotron-nano-12b-v2-vl:free",
                "name": "Nemotron Nano 12B VL (free)",
                "description": "Free vision model from NVIDIA",
                "default": False,
                "free": True,
            },
            {
                "id": "google/gemma-3-vision",
                "name": "Gemma 3 Vision (paid)",
                "description": "Fast vision model — may require credits",
                "default": False,
                "free": False,
            },
            {
                "id": "google/gemini-2.0-flash-001",
                "name": "Gemini 2.0 Flash (paid)",
                "description": "Fast, cost-effective vision model",
                "default": False,
                "free": False,
            },
            {
                "id": "openai/gpt-4o-mini",
                "name": "GPT-4o Mini (paid)",
                "description": "Budget-friendly OpenAI vision model",
                "default": False,
                "free": False,
            },
        ]
    }


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "vision-engine"}


def _detect_image_format(data: bytes) -> Optional[str]:
    if len(data) < 12:
        return None
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        return "png"
    if data[:3] == b'\xff\xd8\xff':
        return "jpeg"
    if data[:6] in (b'GIF87a', b'GIF89a'):
        return "gif"
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return "webp"
    return None
