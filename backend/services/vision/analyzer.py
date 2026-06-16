import asyncio
import base64
import hashlib
import json
import re
from io import BytesIO
from typing import Optional

import httpx
from PIL import Image

from services.vision.models import (
    MarketExtraction,
    MASTER_PROMPT,
    VisionAnalysisResponse,
)
from services.vision.scoring import validate_extraction
from services.vision.validation import SignalValidator

OPENROUTER_BASE = "https://openrouter.ai/api/v1"
_cache: dict[str, VisionAnalysisResponse] = {}
FALLBACK_MODELS = ["nex-agi/nex-n2-pro:free", "openrouter/free"]
RETRY_DELAYS = [2, 5, 10]


def _optimize_image(image_data: bytes, max_width: int = 1024, quality: int = 80) -> bytes:
    img = Image.open(BytesIO(image_data))
    orig_w, orig_h = img.size
    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.LANCZOS)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=quality, optimize=True)
    print(f"[AUDIT] Image: {orig_w}x{orig_h} \u2192 {img.width}x{img.height}, quality={quality}")
    return buffer.getvalue()


def _cache_key(image_data: bytes, model: str) -> str:
    return hashlib.md5(image_data + model.encode()).hexdigest()


class VisionAnalyzer:
    @staticmethod
    async def _do_request(
        client: httpx.AsyncClient,
        api_key: str,
        request_body: dict,
    ) -> httpx.Response:
        sanitized_key = api_key.strip()
        bearer = f"Bearer {sanitized_key}"
        return await client.post(
            f"{OPENROUTER_BASE}/chat/completions",
            headers={
                "Authorization": bearer,
                "Content-Type": "application/json",
                "HTTP-Referer": "scalpex-ai",
            },
            json=request_body,
        )

    @staticmethod
    async def analyze(
        api_key: str,
        image_data: bytes,
        model: str = "openrouter/free",
        prompt: str = "",
    ) -> VisionAnalysisResponse:
        try:
            optimized = _optimize_image(image_data)
        except Exception:
            return VisionAnalysisResponse(
                success=False,
                error="CHART_QUALITY_TOO_LOW: Image could not be processed",
                model=model,
            )
        image_b64 = base64.b64encode(optimized).decode("utf-8")
        image_url = f"data:image/jpeg;base64,{image_b64}"

        ck = _cache_key(optimized, model)
        cached = _cache.get(ck)
        if cached is not None:
            return cached

        system_prompt = prompt if prompt else MASTER_PROMPT

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Analyze this chart using the 12-step master extraction engine. Return only the JSON."},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            },
        ]

        request_body = {
            "model": model,
            "messages": messages,
            "temperature": 0.2,
            "top_p": 0.9,
            "max_tokens": 2000,
        }

        print(f"[AUDIT] model={model}, max_tokens=2000, temperature=0.2, prompt_len={len(system_prompt)}")

        models_to_try = [model] + [m for m in FALLBACK_MODELS if m != model]
        last_error = None

        for attempt_model in models_to_try:
            body = dict(request_body, model=attempt_model)
            ck = _cache_key(optimized, attempt_model)
            cached = _cache.get(ck)
            if cached is not None:
                return cached

            for retry in range(len(RETRY_DELAYS) + 1):
                try:
                    timeout = httpx.Timeout(60.0, connect=15.0)
                    async with httpx.AsyncClient(timeout=timeout) as client:
                        response = await VisionAnalyzer._do_request(client, api_key, body)

                        if response.status_code == 429:
                            if retry < len(RETRY_DELAYS):
                                delay = RETRY_DELAYS[retry]
                                print(f"[RETRY] 429 on {attempt_model}, attempt {retry+1}/{len(RETRY_DELAYS)}, waiting {delay}s")
                                await asyncio.sleep(delay)
                                continue
                            print(f"[RETRY] All 429 retries exhausted for {attempt_model}")
                            last_error = f"429 on {attempt_model}"
                            break

                        if response.status_code == 402:
                            last_error = f"402 on {attempt_model}"
                            break

                        if response.status_code != 200:
                            last_error = f"{response.status_code} on {attempt_model}"
                            print(f"[FALLBACK] {attempt_model} returned {response.status_code}, trying next model")
                            break

                        result_data = response.json()
                        choices = result_data.get("choices", [])
                        if not choices:
                            last_error = f"empty choices on {attempt_model}"
                            print(f"[FALLBACK] {attempt_model} returned no choices, trying next model")
                            break

                        content = choices[0].get("message", {}).get("content", "")
                        if not content:
                            last_error = f"empty content on {attempt_model}"
                            print(f"[FALLBACK] {attempt_model} returned empty content, trying next model")
                            break

                        parsed = VisionAnalyzer._parse_json(content)
                        if parsed is None:
                            last_error = f"unparseable JSON on {attempt_model}"
                            print(f"[FALLBACK] {attempt_model} returned unparseable JSON, trying next model")
                            break

                        parsed = VisionAnalyzer._fill_missing(parsed)

                        try:
                            extraction = MarketExtraction(**parsed)
                        except Exception as e:
                            last_error = f"validation error on {attempt_model}: {e}"
                            print(f"[FALLBACK] {attempt_model} validation error: {e}, trying next model")
                            break

                        # Apply code-level safety net
                        validated_trade = validate_extraction(extraction)
                        extraction.trade = validated_trade

                        # Run 7-layer Signal Validation Engine
                        validation_report = SignalValidator.validate(extraction)

                        result = VisionAnalysisResponse(
                            success=True,
                            extraction=extraction,
                            validation=validation_report,
                            raw=content,
                            model=attempt_model,
                        )
                        _cache[ck] = result
                        return result

                except httpx.TimeoutException:
                    last_error = f"timeout on {attempt_model}"
                    print(f"[FALLBACK] {attempt_model} timed out, trying next model")
                    break
                except Exception as e:
                    last_error = str(e)
                    print(f"[FALLBACK] {attempt_model} error: {e}, trying next model")
                    break

        friendly = "Analysis temporarily unavailable. Please retry shortly."
        return VisionAnalysisResponse(
            success=False,
            error=friendly,
            model=model,
        )

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

    @staticmethod
    def _fill_missing(parsed: dict) -> dict:
        sections = {
            "chartDetection": {
                "exchange": "", "symbol": "", "timeframe": "", "currentPrice": "",
                "sessionType": "", "chartType": "candlestick",
                "exchangeConfidence": 0, "symbolConfidence": 0,
                "timeframeConfidence": 0, "priceConfidence": 0,
            },
            "marketStructure": {
                "higherHighs": False, "higherLows": False,
                "lowerHighs": False, "lowerLows": False,
                "classification": "range", "swingHighs": "", "swingLows": "",
            },
            "liquidity": {
                "buySideLiquidity": "", "sellSideLiquidity": "",
                "equalHighs": False, "equalLows": False,
                "stopClusters": "", "liquidityPools": "",
                "internalLiquidity": "", "externalLiquidity": "",
                "swept": False, "sweepType": "none",
            },
            "smc": {
                "bos": "", "choch": "", "mss": "",
                "bosConfidence": 0, "chochConfidence": 0, "mssConfidence": 0,
            },
            "premiumDiscount": {
                "dealingRange": "", "equilibrium": "",
                "premiumZone": "", "discountZone": "",
                "currentPosition": "equilibrium",
            },
            "volume": {
                "spikes": "", "absorption": "", "exhaustion": "",
                "breakoutVolume": "", "weakVolume": "", "climaxVolume": "",
            },
            "momentum": {
                "impulsive": "", "corrective": "", "consolidation": "",
                "compression": "", "score": 0,
            },
            "trade": {
                "bias": "NO_TRADE", "confidence": 0,
                "entry": "", "stop": "", "tp1": "", "tp2": "", "tp3": "",
                "riskReward": "", "probabilityScore": "",
                "reasoning": [],
            },
            "scoring": {
                "marketStructure": 0, "liquidity": 0, "fvg": 0,
                "orderBlocks": 0, "volume": 0, "momentum": 0, "total": 0,
            },
        }
        for section, defaults in sections.items():
            if section not in parsed or not isinstance(parsed[section], dict):
                parsed[section] = {}
            if section == "fvgs" and section not in parsed:
                parsed[section] = []
            if section == "orderBlocks" and section not in parsed:
                parsed[section] = []
            for k, v in defaults.items():
                parsed[section].setdefault(k, v)
        return parsed
