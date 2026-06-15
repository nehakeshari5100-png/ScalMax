
"""
FastAPI router for the Gemma Vision Analysis Engine.

Endpoints:
- POST /analyze — Upload a chart image for AI vision analysis
- GET  /health — Health check
"""

import base64
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from services.vision.analyzer import VisionAnalyzer
from services.vision.models import VisionAnalysisResponse

router = APIRouter(tags=["vision"])

ALLOWED_FORMATS = {"png", "jpeg", "jpg", "gif", "webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/analyze", response_model=VisionAnalysisResponse)
async def analyze_chart(
    file: UploadFile = File(...),
    api_key: str = Form(...),
    model: str = Form("google/gemma-3-vision"),
    prompt: str = Form(""),
):
    """
    Upload a chart screenshot for vision-based analysis.

    Accepts PNG, JPEG, GIF, WEBP up to 10MB.
    Returns structured JSON with trend, structure, liquidity,
    support/resistance, entry ideas, risk zones, and confidence.
    """
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    # Read file content
    image_data = await file.read()

    if len(image_data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // 1024 // 1024}MB",
        )

    # Detect image format via magic bytes (imghdr removed in Python 3.13+)
    img_format = _detect_image_format(image_data)
    if img_format is None:
        # Try from extension
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

    # Encode as base64
    image_base64 = base64.b64encode(image_data).decode("utf-8")

    # Run analysis
    result = await VisionAnalyzer.analyze(
        api_key=api_key,
        image_base64=image_base64,
        model=model,
        prompt=prompt,
    )

    if not result.success:
        return result

    return result


@router.get("/models")
async def list_vision_models():
    """List recommended vision-capable models for chart analysis."""
    return {
        "models": [
            {
                "id": "google/gemma-3-27b-it",
                "name": "Gemma 3 27B",
                "description": "Latest Gemma vision model — good for chart analysis",
                "default": True,
            },
            {
                "id": "google/gemini-2.0-flash-001",
                "name": "Gemini 2.0 Flash",
                "description": "Fast, cost-effective vision model",
                "default": False,
            },
            {
                "id": "openai/gpt-4o",
                "name": "GPT-4o",
                "description": "Best-in-class vision analysis",
                "default": False,
            },
            {
                "id": "openai/gpt-4o-mini",
                "name": "GPT-4o Mini",
                "description": "Budget-friendly vision model",
                "default": False,
            },
            {
                "id": "anthropic/claude-3.5-sonnet",
                "name": "Claude 3.5 Sonnet",
                "description": "Strong chart reading capabilities",
                "default": False,
            },
        ]
    }


@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "vision-engine"}


def _detect_image_format(data: bytes) -> Optional[str]:
    """Detect image format from magic bytes (portable imghdr replacement)."""
    if len(data) < 12:
        return None
    # PNG: 89 50 4E 47 0D 0A 1A 0A
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        return "png"
    # JPEG: FF D8 FF
    if data[:3] == b'\xff\xd8\xff':
        return "jpeg"
    # GIF87a: 47 49 46 38 37 61
    if data[:6] in (b'GIF87a', b'GIF89a'):
        return "gif"
    # WEBP: RIFF .... WEBP (8 bytes in)
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return "webp"
    return None
