import asyncio
import base64
import hashlib
import json
import re
import time
import traceback
from io import BytesIO
from typing import Optional

import httpx
from PIL import Image

from services.vision.models import (
    MarketExtraction,
    InstitutionalDecision,
    ConfidenceScores,
    ConflictReport,
    LiquidityTarget,
    ExecutionPlan,
    TradePlan,
    INSTITUTIONAL_PROMPT,
    VisionAnalysisResponse,
)
from services.vision.scoring import validate_extraction
from services.vision.validation import SignalValidator

OPENROUTER_BASE = "https://openrouter.ai/api/v1"
_cache: dict[str, VisionAnalysisResponse] = {}
FALLBACK_MODELS = ["google/gemma-4-31b-it:free", "openrouter/free"]
RETRY_DELAYS = [2, 5, 10]


def _optimize_image(image_data: bytes, max_width: int = 1024, quality: int = 75) -> bytes:
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
    kb = len(buffer.getvalue()) / 1024
    print(f"[PROFILE] Image: {orig_w}x{orig_h} -> {img.width}x{img.height}, q={quality}, {kb:.1f}KB")
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
        _TOTAL = time.time()
        print("[PROFILE] === BACKEND ENTRY ===")
        try:
            optimized = _optimize_image(image_data)
            t_img = time.time()
            print(f"[PROFILE] Image optimized: {len(optimized)} bytes ({len(image_data)/1024:.0f}KB -> {len(optimized)/1024:.0f}KB, {(t_img-_TOTAL)*1000:.0f}ms)")
        except Exception as e:
            print(f"[PIPELINE] Image optimization FAILED: {e}")
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
            print("[PIPELINE] Cache HIT, returning cached result")
            return cached

        system_prompt = prompt if prompt else INSTITUTIONAL_PROMPT

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Analyze this chart using the 10-step institutional trade decision engine. Return only the JSON."},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            },
        ]

        request_body = {
            "model": model,
            "messages": messages,
            "temperature": 0.1,
            "top_p": 0.9,
            "max_tokens": 600,
        }

        print(f"[PROFILE] model={model}, max_tokens=600, temperature=0.1, prompt_len={len(system_prompt)}")

        models_to_try = [model] + [m for m in FALLBACK_MODELS if m != model]
        last_error = None
        last_detail = None

        for attempt_model in models_to_try:
            body = dict(request_body, model=attempt_model)
            ck = _cache_key(optimized, attempt_model)
            cached = _cache.get(ck)
            if cached is not None:
                print(f"[PIPELINE] Cache HIT for {attempt_model}")
                return cached

            for retry in range(len(RETRY_DELAYS) + 1):
                try:
                    timeout = httpx.Timeout(20.0, connect=10.0)
                    print(f"[PROFILE] OpenRouter request: model={attempt_model}, attempt={retry+1}/30s-timeout")
                    t0 = time.time()
                    async with httpx.AsyncClient(timeout=timeout) as client:
                        response = await VisionAnalyzer._do_request(client, api_key, body)
                    t1 = time.time()
                    roundtrip_ms = (t1-t0)*1000
                    print(f"[PROFILE] OpenRouter response: HTTP {response.status_code}, took {roundtrip_ms:.0f}ms")

                    if response.status_code != 200:
                        err_body = ""
                        try: err_body = response.text[:200]
                        except: pass
                        print(f"[PIPELINE] Non-200 on {attempt_model}: {response.status_code}, body={err_body}")
                        if response.status_code == 429:
                            if retry < len(RETRY_DELAYS):
                                delay = RETRY_DELAYS[retry]
                                print(f"[PIPELINE] 429 on {attempt_model}, retry {retry+1}/{len(RETRY_DELAYS)}, waiting {delay}s")
                                await asyncio.sleep(delay)
                                continue
                            print(f"[PIPELINE] All 429 retries exhausted for {attempt_model}")
                            last_error = f"429 on {attempt_model}: {err_body[:200]}"
                            last_detail = {"originalError": f"HTTP 429 (rate limited): {err_body[:200]}", "statusCode": 429, "source": "OpenRouter API", "model": attempt_model, "providerResponse": err_body[:200], "stage": "openrouter_request"}
                            break
                        if response.status_code == 402:
                            print(f"[PIPELINE] 402 (insufficient credits) on {attempt_model}")
                            last_error = f"402 on {attempt_model}: {err_body[:200]}"
                            last_detail = {"originalError": f"HTTP 402 (insufficient credits): {err_body[:200]}", "statusCode": 402, "source": "OpenRouter API", "model": attempt_model, "providerResponse": err_body[:200], "stage": "openrouter_request"}
                            break
                        last_error = f"{response.status_code} on {attempt_model}: {err_body[:200]}"
                        last_detail = {"originalError": f"HTTP {response.status_code}: {err_body[:200]}", "statusCode": response.status_code, "source": "OpenRouter API", "model": attempt_model, "providerResponse": err_body[:200], "stage": "openrouter_request"}
                        print(f"[PIPELINE] Non-200, trying next model")
                        break

                    print("[PROFILE] Parsing JSON response body")
                    t2 = time.time()
                    result_data = response.json()
                    parse_ms = (time.time()-t2)*1000
                    print(f"[PROFILE] JSON parsed in {parse_ms:.0f}ms")

                    choices = result_data.get("choices", [])
                    if not choices:
                        resp_str = str(result_data)[:200]
                        last_error = f"empty choices on {attempt_model}"
                        last_detail = {"originalError": f"OpenRouter returned 0 choices in response", "statusCode": 200, "source": "OpenRouter response parser", "model": attempt_model, "providerResponse": resp_str, "stage": "parse_choices"}
                        print(f"[PIPELINE] No choices in response: {resp_str}")
                        break

                    content = choices[0].get("message", {}).get("content", "")
                    if not content:
                        msg_str = str(choices[0].get("message", {}))[:200]
                        last_error = f"empty content on {attempt_model}"
                        last_detail = {"originalError": f"message content is empty/null", "statusCode": 200, "source": "OpenRouter response parser", "model": attempt_model, "providerResponse": msg_str, "stage": "parse_content"}
                        print(f"[PIPELINE] Empty message content: {msg_str}")
                        break

                    print(f"[PROFILE] Content length: {len(content)} chars")

                    parsed = VisionAnalyzer._parse_json(content)
                    if parsed is None:
                        last_error = f"unparseable JSON on {attempt_model}"
                        last_detail = {"originalError": "Model returned non-JSON content that could not be parsed", "statusCode": 200, "source": "JSON parser", "model": attempt_model, "providerResponse": content[:300], "stage": "parse_json"}
                        print(f"[PIPELINE] JSON parsing FAILED. Raw content[:300]={content[:300]}")
                        break

                    print(f"[PIPELINE] JSON keys: {list(parsed.keys())}")

                    parsed = VisionAnalyzer._fill_missing(parsed)

                    try:
                        extraction = MarketExtraction(**parsed)
                        print(f"[PIPELINE] MarketExtraction created: bias={extraction.trade.bias}, confidence={extraction.trade.confidence}")
                    except Exception as e:
                        last_error = f"validation error on {attempt_model}: {e}"
                        last_detail = {"originalError": str(e), "statusCode": None, "source": "MarketExtraction pydantic validation", "model": attempt_model, "providerResponse": str(parsed)[:300], "stage": "pydantic_validation", "stackTrace": traceback.format_exc()}
                        print(f"[PIPELINE] MarketExtraction validation FAILED: {e}")
                        traceback.print_exc()
                        break

                    # Map institutional decision back to TradePlan for backward compat
                    inst = extraction.institutionalDecision
                    if inst is not None and inst.tradePlan is not None:
                        tp = inst.tradePlan
                        tp.riskReward = inst.riskReward or tp.riskReward
                        tp.probabilityScore = inst.probabilityScore or tp.probabilityScore
                        if inst.confidence and inst.confidence.total > 0:
                            tp.confidence = inst.confidence.total
                        if inst.reasoning:
                            tp.reasoning = inst.reasoning
                        extraction.trade = tp
                    elif inst is not None and inst.bias == "NO_TRADE":
                        extraction.trade.bias = "NO_TRADE"
                        extraction.trade.confidence = 0

                    print("[PIPELINE] Running validate_extraction()")
                    validated_trade = validate_extraction(extraction)
                    extraction.trade = validated_trade

                    print("[PIPELINE] Running SignalValidator.validate()")
                    try:
                        validation_report = SignalValidator.validate(extraction)
                    except Exception as e:
                        last_error = f"validation error on {attempt_model}: {e}"
                        last_detail = {"originalError": str(e), "statusCode": None, "source": "SignalValidator.validate()", "model": attempt_model, "providerResponse": str(extraction.dict() if hasattr(extraction, 'dict') else extraction)[:300], "stage": "signal_validation", "stackTrace": traceback.format_exc()}
                        print(f"[PIPELINE] SignalValidator FAILED: {e}")
                        traceback.print_exc()
                        break
                    print(f"[PIPELINE] Validation: finalScore={validation_report.finalScore}, strength={validation_report.signalStrength}")

                    _total_ms = (time.time() - _TOTAL) * 1000
                    print(f"[PROFILE] === BACKEND TOTAL: {_total_ms:.0f}ms ===")
                    result = VisionAnalysisResponse(
                        success=True,
                        extraction=extraction,
                        validation=validation_report,
                        raw=content,
                        model=attempt_model,
                    )
                    _cache[ck] = result
                    print(f"[PROFILE] BACKEND SUCCESS ({_total_ms:.0f}ms): {attempt_model}")
                    return result

                except httpx.TimeoutException:
                    last_error = f"timeout on {attempt_model}"
                    last_detail = {"originalError": f"httpx.TimeoutException after 30s", "statusCode": None, "source": "httpx request", "model": attempt_model, "providerResponse": "", "stage": "openrouter_request_timeout"}
                    print(f"[PIPELINE] TIMEOUT on {attempt_model} (30s), trying next model")
                    break
                except Exception as e:
                    last_error = str(e)
                    last_detail = {"originalError": f"{type(e).__name__}: {e}", "statusCode": None, "source": f"unhandled exception in {attempt_model} loop", "model": attempt_model, "providerResponse": "", "stage": "unhandled_exception", "stackTrace": traceback.format_exc()}
                    print(f"[PIPELINE] ERROR on {attempt_model}: {type(e).__name__}: {e}")
                    traceback.print_exc()
                    break

        _total_ms = (time.time() - _TOTAL) * 1000
        print(f"[PROFILE] === BACKEND FAILED ({_total_ms:.0f}ms): {last_error}")
        return VisionAnalysisResponse(
            success=False,
            error=last_error or "Analysis failed with no specific error",
            detail=last_detail,
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

        # Fill institutionalDecision defaults if present
        inst = parsed.get("institutionalDecision")
        if inst is not None and isinstance(inst, dict):
            inst.setdefault("marketState", "")
            inst.setdefault("bias", "NO_TRADE")
            inst.setdefault("tradeGrade", "")
            inst.setdefault("riskReward", "")
            inst.setdefault("probabilityScore", "")
            inst.setdefault("reasoning", [])
            inst_confidence = inst.get("confidence")
            if inst_confidence is None or not isinstance(inst_confidence, dict):
                inst["confidence"] = {"structure": 0, "liquidity": 0, "smc": 0, "volume": 0, "momentum": 0, "rr": 0, "total": 0}
            inst_trade = inst.get("tradePlan")
            if inst_trade is None or not isinstance(inst_trade, dict):
                inst["tradePlan"] = {"bias": "NO_TRADE", "confidence": 0, "entry": "", "stop": "", "tp1": "", "tp2": "", "tp3": "", "riskReward": "", "probabilityScore": "", "reasoning": []}
            inst_conflict = inst.get("conflictReport")
            if inst_conflict is None or not isinstance(inst_conflict, dict):
                inst["conflictReport"] = {"bullishFactors": [], "bearishFactors": [], "highConflict": False}
            inst_liq = inst.get("liquidityTarget")
            if inst_liq is None or not isinstance(inst_liq, dict):
                inst["liquidityTarget"] = {"nearest": "", "major": "", "final": ""}
            inst_exec = inst.get("executionPlan")
            if inst_exec is None or not isinstance(inst_exec, dict):
                inst["executionPlan"] = {"entryTrigger": "", "invalidation": "", "targetLogic": ""}

        return parsed
