"""Vision Analysis Engine — sends chart images to OpenRouter and extracts structured observations."""

import base64
import hashlib
import json
import re
from io import BytesIO
from typing import Optional

import httpx
from PIL import Image

from services.vision.models import (
    VisionObservation,
    OBSERVATION_PROMPT,
    VisionAnalysisResponse,
)

OPENROUTER_BASE = "https://openrouter.ai/api/v1"
_cache: dict[str, VisionAnalysisResponse] = {}


def _optimize_image(image_data: bytes, max_width: int = 800, quality: int = 55) -> bytes:
    """Resize to max_width, convert to JPEG quality, strip metadata."""
    img = Image.open(BytesIO(image_data))
    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.LANCZOS)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=quality, optimize=True)
    return buffer.getvalue()


def _cache_key(image_data: bytes, model: str) -> str:
    return hashlib.md5(image_data + model.encode()).hexdigest()


class VisionAnalyzer:
    """Sends chart images to OpenRouter vision models and extracts observations."""

    @staticmethod
    async def analyze(
        api_key: str,
        image_data: bytes,
        model: str = "openrouter/free",
        prompt: str = "",
    ) -> VisionAnalysisResponse:
        """Analyze a chart image and return structured observations."""
        optimized = _optimize_image(image_data)
        image_b64 = base64.b64encode(optimized).decode("utf-8")
        image_url = f"data:image/jpeg;base64,{image_b64}"

        ck = _cache_key(optimized, model)
        cached = _cache.get(ck)
        if cached is not None:
            return cached

        system_prompt = prompt if prompt else OBSERVATION_PROMPT

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract observations from this chart. Return only JSON."},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            },
        ]

        request_body = {
            "model": model,
            "messages": messages,
            "temperature": 0.2,
            "top_p": 0.8,
            "max_tokens": 150,
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{OPENROUTER_BASE}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "scalpex-ai",
                    },
                    json=request_body,
                )

                if response.status_code == 402:
                    # Auto-retry with free router if not already using it
                    if model != "openrouter/free":
                        free_result = await VisionAnalyzer.analyze(
                            api_key=api_key,
                            image_data=image_data,
                            model="openrouter/free",
                            prompt=prompt,
                        )
                        return free_result
                    result = VisionAnalysisResponse(
                        success=False,
                        error="Insufficient OpenRouter credits. Switch to 'openrouter/free' model or add credits at https://openrouter.ai/settings/credits.",
                        model=model,
                    )
                    _cache[ck] = result
                    return result

                if response.status_code != 200:
                    error_detail = response.text
                    try:
                        err_json = response.json()
                        error_detail = err_json.get("error", {}).get("message", response.text)
                    except Exception:
                        pass
                    result = VisionAnalysisResponse(
                        success=False,
                        error=f"OpenRouter API error ({response.status_code}): {error_detail}",
                        model=model,
                    )
                    _cache[ck] = result
                    return result

                result_data = response.json()
                choices = result_data.get("choices", [])
                if not choices:
                    result = VisionAnalysisResponse(
                        success=False,
                        error="No choices in OpenRouter response",
                        raw=json.dumps(result_data),
                        model=model,
                    )
                    _cache[ck] = result
                    return result

                content = choices[0].get("message", {}).get("content", "")
                if not content:
                    result = VisionAnalysisResponse(
                        success=False,
                        error="Empty response from model",
                        raw=json.dumps(result_data),
                        model=model,
                    )
                    _cache[ck] = result
                    return result

                parsed = VisionAnalyzer._parse_json(content)
                if parsed is None:
                    result = VisionAnalysisResponse(
                        success=False,
                        error="Failed to parse JSON from model response",
                        raw=content,
                        model=model,
                    )
                    _cache[ck] = result
                    return result

                observation = VisionObservation(**parsed)
                result = VisionAnalysisResponse(
                    success=True,
                    observation=observation,
                    raw=content,
                    model=model,
                )
                _cache[ck] = result
                return result

        except httpx.TimeoutException:
            result = VisionAnalysisResponse(
                success=False,
                error="Request timed out after 60 seconds",
                model=model,
            )
            _cache[ck] = result
            return result
        except Exception as e:
            result = VisionAnalysisResponse(
                success=False,
                error=f"Analysis failed: {str(e)}",
                model=model,
            )
            _cache[ck] = result
            return result

    @staticmethod
    def _parse_json(content: str) -> Optional[dict]:
        content = content.strip()
        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", content, re.DOTALL)
        if match:
            content = match.group(1).strip()
        brace_start = content.find("{")
        brace_end = content.rfind("}")
        if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
            try:
                return json.loads(content[brace_start: brace_end + 1])
            except json.JSONDecodeError:
                pass
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return None
