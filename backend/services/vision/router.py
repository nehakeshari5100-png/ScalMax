from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from services.vision.analyzer import VisionAnalyzer
from services.vision.models import VisionAnalysisResponse

router = APIRouter(tags=["vision"])

ALLOWED_FORMATS = {"png", "jpeg", "jpg", "gif", "webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024


@router.post("/analyze", response_model=VisionAnalysisResponse)
async def analyze_chart(
    file: UploadFile = File(...),
    api_key: str = Form(...),
    model: str = Form("google/gemma-4-31b-it:free"),
    prompt: str = Form(""),
):
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

    result = await VisionAnalyzer.analyze(
        api_key=api_key,
        image_data=image_data,
        model=model,
        prompt=prompt,
    )

    return result


@router.get("/models")
async def list_vision_models():
    return {
        "models": [
            {
                "id": "openrouter/free",
                "name": "OpenRouter Free Router",
                "description": "Auto-routes to best free vision model",
                "default": False,
                "free": True,
            },
            {
                "id": "google/gemma-4-26b-a4b-it:free",
                "name": "Gemma 4 26B (free)",
                "description": "Free vision model from Google",
                "default": False,
                "free": True,
            },
            {
                "id": "google/gemma-4-31b-it:free",
                "name": "Nex AGI Nex-N2-Pro (free)",
                "description": "Free vision MoE model",
                "default": True,
                "free": True,
            },
            {
                "id": "openai/gpt-4o-mini",
                "name": "GPT-4o Mini (paid)",
                "description": "Budget-friendly OpenAI vision model",
                "default": False,
                "free": False,
            }
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
