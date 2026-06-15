
"""
Vision Analysis Engine — sends chart screenshots to OpenRouter
vision-capable models and returns structured JSON analysis.

Supports:
- Gemma 3 Vision (default)
- Any vision model available through OpenRouter
- Image base64 encoding
- Configurable prompt
- Strict JSON-only output parsing
"""

import json
import re
from typing import Optional

import httpx

from services.vision.models import (
    ChartAnalysisResult,
    DEFAULT_SYSTEM_PROMPT,
    VisionAnalysisResponse,
)

OPENROUTER_BASE = "https://openrouter.ai/api/v1"


class VisionAnalyzer:
    """
    Sends chart images to OpenRouter vision models and parses
    the structured JSON response.

    The analyzer acts ONLY as a chart analyst — it never generates
    trading signals or buy/sell recommendations.
    """

    @staticmethod
    async def analyze(
        api_key: str,
        image_base64: str,
        model: str = "google/gemma-3-vision",
        prompt: str = "",
    ) -> VisionAnalysisResponse:
        """
        Analyze a chart image using the specified vision model.

        Args:
            api_key: OpenRouter API key
            image_base64: Base64-encoded image data
            model: OpenRouter model identifier (default: Gemma 3 27B)
            prompt: Optional custom prompt; uses default if empty

        Returns:
            VisionAnalysisResponse with parsed ChartAnalysisResult
        """
        system_prompt = prompt if prompt else DEFAULT_SYSTEM_PROMPT

        # Build OpenAI-compatible vision messages
        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Analyze this chart image. Return only JSON.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}"
                        },
                    },
                ],
            },
        ]

        request_body = {
            "model": model,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 2000,
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

                if response.status_code != 200:
                    error_detail = response.text
                    try:
                        err_json = response.json()
                        error_detail = err_json.get("error", {}).get(
                            "message", response.text
                        )
                    except Exception:
                        pass
                    return VisionAnalysisResponse(
                        success=False,
                        error=f"OpenRouter API error ({response.status_code}): {error_detail}",
                        model=model,
                    )

                result = response.json()

                # Extract content from response
                choices = result.get("choices", [])
                if not choices:
                    return VisionAnalysisResponse(
                        success=False,
                        error="No choices in OpenRouter response",
                        raw=json.dumps(result),
                        model=model,
                    )

                content = choices[0].get("message", {}).get("content", "")
                if not content:
                    return VisionAnalysisResponse(
                        success=False,
                        error="Empty response from model",
                        raw=json.dumps(result),
                        model=model,
                    )

                # Parse JSON from response
                parsed = VisionAnalyzer._parse_json(content)
                if parsed is None:
                    return VisionAnalysisResponse(
                        success=False,
                        error="Failed to parse JSON from model response",
                        raw=content,
                        model=model,
                    )

                analysis = ChartAnalysisResult(**parsed)

                return VisionAnalysisResponse(
                    success=True,
                    data=analysis,
                    raw=content,
                    model=model,
                )

        except httpx.TimeoutException:
            return VisionAnalysisResponse(
                success=False,
                error="Request timed out after 60 seconds",
                model=model,
            )
        except Exception as e:
            return VisionAnalysisResponse(
                success=False,
                error=f"Analysis failed: {str(e)}",
                model=model,
            )

    @staticmethod
    def _parse_json(content: str) -> Optional[dict]:
        """
        Extract a JSON object from the model's response text.

        Handles:
        - Pure JSON output
        - JSON wrapped in markdown code blocks (```json ... ```)
        - JSON with surrounding text
        """
        # Try direct parse first
        content = content.strip()

        # Remove markdown code block fences
        code_block_pattern = r"```(?:json)?\s*\n?(.*?)\n?```"
        match = re.search(code_block_pattern, content, re.DOTALL)
        if match:
            content = match.group(1).strip()

        # Find JSON object boundaries
        brace_start = content.find("{")
        brace_end = content.rfind("}")

        if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
            json_str = content[brace_start : brace_end + 1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        # Final attempt: try parsing the whole content
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return None
