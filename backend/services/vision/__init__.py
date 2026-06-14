
"""
Gemma Vision Analysis Engine — analyzes chart screenshots using
vision-capable OpenRouter models.

Returns structured JSON analysis of trend, market structure,
liquidity, support/resistance, entry ideas, and risk zones.

Usage:
    POST /api/v1/vision/analyze  (multipart: file + api_key + model)
"""

from services.vision.analyzer import VisionAnalyzer
from services.vision.models import (
    ChartAnalysisResult,
    VisionAnalysisRequest,
    VisionAnalysisResponse,
    DEFAULT_SYSTEM_PROMPT,
)

__all__ = [
    "VisionAnalyzer",
    "ChartAnalysisResult",
    "VisionAnalysisRequest",
    "VisionAnalysisResponse",
    "DEFAULT_SYSTEM_PROMPT",
]
