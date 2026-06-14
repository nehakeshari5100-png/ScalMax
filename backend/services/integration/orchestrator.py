import time
import uuid
import logging
from typing import Optional, List

from services.market_data.models import Candle
from services.integration.models import (
    PipelineRequest, PipelineResponse, PipelineResult, PipelineStage,
)
from services.integration.data_provider import DataProvider
from services.integration.market_structure import analyze_market_structure

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """
    End-to-end pipeline orchestrator.

    Runs all engines in sequence:
      1. Market Data  → fetch candles
      2. Indicators   → compute all technical indicators
      3. Liquidity    → detect FVG, OBs, sweeps, pools
      4. Structure    → detect swing highs/lows, regime
      5. Confluence   → score all signals together
      6. Vision       → (optional) analyze chart via OpenRouter
      7. Decision     → master AI decision
      8. Signal       → generate + persist signal record
    """

    @staticmethod
    async def run(request: PipelineRequest) -> PipelineResponse:
        exec_id = str(uuid.uuid4())
        stages: List[PipelineResult] = []
        start = time.time()

        # ── Stage 1: Fetch Candles ──
        candles = []
        s1_start = time.time()
        try:
            candles = await DataProvider.fetch_candles(
                request.symbol, request.timeframe, request.exchange, request.lookback,
            )
            stages.append(PipelineResult(
                stage=PipelineStage.FETCH_CANDLES,
                status="completed",
                duration_ms=(time.time() - s1_start) * 1000,
                data={"count": len(candles)},
            ))
        except Exception as e:
            stages.append(PipelineResult(
                stage=PipelineStage.FETCH_CANDLES,
                status="failed",
                duration_ms=(time.time() - s1_start) * 1000,
                error=str(e),
            ))
            return PipelineResponse(
                success=False, execution_id=exec_id,
                symbol=request.symbol, timeframe=request.timeframe,
                exchange=request.exchange, stages=stages,
                error=f"Failed to fetch candles: {e}",
            )

        if len(candles) < 10:
            return PipelineResponse(
                success=False, execution_id=exec_id,
                symbol=request.symbol, timeframe=request.timeframe,
                exchange=request.exchange, stages=stages,
                error="Insufficient candle data (< 10)",
            )

        closes = [c.close for c in candles]
        highs = [c.high for c in candles]
        lows = [c.low for c in candles]
        opens = [c.open for c in candles]
        volumes = [c.volume for c in candles]
        current_price = closes[-1]

        # ── Stage 2: Calculate Indicators ──
        s2_start = time.time()
        indicator_set = None
        try:
            from services.indicators import IndicatorEngine
            engine = IndicatorEngine()
            indicator_set = await engine.calculate_from_candles(
                request.symbol, request.timeframe, candles,
            )
            stages.append(PipelineResult(
                stage=PipelineStage.CALCULATE_INDICATORS,
                status="completed",
                duration_ms=(time.time() - s2_start) * 1000,
                data={
                    "trend_score": indicator_set.trend_score,
                    "momentum_score": indicator_set.momentum_score,
                    "volatility_score": indicator_set.volatility_score,
                },
            ))
        except Exception as e:
            logger.warning(f"Indicator calculation failed: {e}")
            stages.append(PipelineResult(
                stage=PipelineStage.CALCULATE_INDICATORS,
                status="failed", duration_ms=(time.time() - s2_start) * 1000, error=str(e),
            ))

        # ── Stage 3: Detect Liquidity ──
        s3_start = time.time()
        liquidity_map = None
        try:
            from services.liquidity import build_liquidity_map
            liquidity_map = build_liquidity_map(
                request.symbol, request.timeframe,
                highs, lows, closes, opens, volumes,
            )
            stages.append(PipelineResult(
                stage=PipelineStage.DETECT_LIQUIDITY,
                status="completed",
                duration_ms=(time.time() - s3_start) * 1000,
                data={
                    "fvg_count": len(liquidity_map.fvg),
                    "order_block_count": len(liquidity_map.order_blocks),
                    "sweep_count": len(liquidity_map.liquidity_sweeps),
                    "confidence": liquidity_map.overall_confidence,
                },
            ))
        except Exception as e:
            logger.warning(f"Liquidity detection failed: {e}")
            stages.append(PipelineResult(
                stage=PipelineStage.DETECT_LIQUIDITY,
                status="failed", duration_ms=(time.time() - s3_start) * 1000, error=str(e),
            ))

        # ── Stage 4: Market Structure Analysis ──
        s4_start = time.time()
        ms = None
        try:
            ms = analyze_market_structure(closes, highs, lows)
            stages.append(PipelineResult(
                stage=PipelineStage.ANALYZE_STRUCTURE,
                status="completed",
                duration_ms=(time.time() - s4_start) * 1000,
                data={
                    "trend_direction": ms.trend_direction,
                    "regime": ms.market_regime,
                    "swing_highs": ms.swing_highs,
                    "swing_lows": ms.swing_lows,
                    "structure_score": ms.structure_score,
                },
            ))
        except Exception as e:
            logger.warning(f"Market structure analysis failed: {e}")
            stages.append(PipelineResult(
                stage=PipelineStage.ANALYZE_STRUCTURE,
                status="failed", duration_ms=(time.time() - s4_start) * 1000, error=str(e),
            ))

        # ── Stage 5: Confluence Scoring ──
        s5_start = time.time()
        confluence_output = None
        try:
            from services.confluence import score_confluence, ConfluenceInput
            ci = ConfluenceInput(
                symbol=request.symbol,
                timeframe=request.timeframe,
                trend_score=indicator_set.trend_score if indicator_set else 0,
                momentum_score=indicator_set.momentum_score if indicator_set else 0,
                volume_score=min(100, (indicator_set.volume_spike.ratio * 50)) if indicator_set and indicator_set.volume_spike else 0,
                volatility_score=indicator_set.volatility_score if indicator_set else 0,
                rsi=indicator_set.rsi if indicator_set else None,
                macd_histogram=indicator_set.macd.histogram if indicator_set and indicator_set.macd else None,
                ema9=indicator_set.ema9 if indicator_set else None,
                ema20=indicator_set.ema20 if indicator_set else None,
                ema50=indicator_set.ema50 if indicator_set else None,
                price=current_price,
                atr_percent=indicator_set.atr_percent if indicator_set else None,
                volume_spike_ratio=indicator_set.volume_spike.ratio if indicator_set and indicator_set.volume_spike else None,
                market_structure=ms or type('obj', (object,), {})(),
                liquidity_confidence=liquidity_map.overall_confidence if liquidity_map else 0,
                fvg_count=len(liquidity_map.fvg) if liquidity_map else 0,
                order_block_count=len(liquidity_map.order_blocks) if liquidity_map else 0,
                breaker_block_count=len(liquidity_map.breaker_blocks) if liquidity_map else 0,
                sweep_count=len(liquidity_map.liquidity_sweeps) if liquidity_map else 0,
                equal_high_count=len(liquidity_map.equal_highs) if liquidity_map else 0,
                equal_low_count=len(liquidity_map.equal_lows) if liquidity_map else 0,
                bullish_liquidity_pools=len(liquidity_map.bullish_liquidity) if liquidity_map else 0,
                bearish_liquidity_pools=len(liquidity_map.bearish_liquidity) if liquidity_map else 0,
            )
            ci.market_structure = ms
            confluence_output = score_confluence(ci)
            stages.append(PipelineResult(
                stage=PipelineStage.SCORE_CONFLUENCE,
                status="completed",
                duration_ms=(time.time() - s5_start) * 1000,
                data={
                    "score": confluence_output.score,
                    "grade": confluence_output.grade,
                    "direction": confluence_output.direction,
                },
            ))
        except Exception as e:
            logger.warning(f"Confluence scoring failed: {e}")
            stages.append(PipelineResult(
                stage=PipelineStage.SCORE_CONFLUENCE,
                status="failed", duration_ms=(time.time() - s5_start) * 1000, error=str(e),
            ))

        # ── Stage 6: Vision Analysis (optional) ──
        vision_result = None
        if request.include_vision and request.chart_image_base64:
            s6_start = time.time()
            try:
                from services.vision.router import analyze_chart as analyze_image
                vision_result = await analyze_image(
                    request.chart_image_base64,
                    request.api_key or "",
                    request.vision_model,
                )
                stages.append(PipelineResult(
                    stage=PipelineStage.ANALYZE_VISION,
                    status="completed",
                    duration_ms=(time.time() - s6_start) * 1000,
                    data={"confidence": vision_result.get("confidence", 0) if vision_result else 0},
                ))
            except Exception as e:
                logger.warning(f"Vision analysis failed: {e}")
                stages.append(PipelineResult(
                    stage=PipelineStage.ANALYZE_VISION,
                    status="failed", duration_ms=(time.time() - s6_start) * 1000, error=str(e),
                ))

        # ── Stage 7: Master Decision ──
        s7_start = time.time()
        decision_output = None
        try:
            from services.decision import MasterDecisionEngine, DecisionInput, VisionInterpretation, DeterministicAssessment
            di = DecisionInput(
                symbol=request.symbol,
                timeframe=request.timeframe,
                exchange=request.exchange,
                price=current_price,
                include_vision=request.include_vision,
                api_key=request.api_key,
                vision_model=request.vision_model,
            )
            if confluence_output:
                di.deterministic_override = DeterministicAssessment(
                    direction=confluence_output.direction,
                    confidence=confluence_output.score,
                    confluence_score=confluence_output.score,
                    confluence_grade=confluence_output.grade,
                    trend_score=indicator_set.trend_score if indicator_set else 0,
                    momentum_score=indicator_set.momentum_score if indicator_set else 0,
                    volume_score=min(100, (indicator_set.volume_spike.ratio * 50)) if indicator_set and indicator_set.volume_spike else 0,
                    volatility_score=indicator_set.volatility_score if indicator_set else 0,
                    liquidity_confidence=liquidity_map.overall_confidence if liquidity_map else 0,
                    market_structure_score=ms.structure_score if ms else 0,
                    reasons=confluence_output.reasons,
                    risks=confluence_output.risks,
                )
            if vision_result:
                vision_dir = vision_result.get("direction", "neutral")
                vision_trend = {
                    "long": "Uptrend — bullish microstructure and liquidity sweep",
                    "short": "Downtrend — bearish microstructure and liquidity sweep",
                    "neutral": "Ranging — no clear directional bias",
                }.get(vision_dir, "")
                di.vision_analysis = VisionInterpretation(
                    trend=vision_trend,
                    confidence=vision_result.get("confidence", 0),
                    support_zones=vision_result.get("supportZones", []),
                    resistance_zones=vision_result.get("resistanceZones", []),
                )

            decision_output = MasterDecisionEngine.decide(di)
            stages.append(PipelineResult(
                stage=PipelineStage.MAKE_DECISION,
                status="completed",
                duration_ms=(time.time() - s7_start) * 1000,
                data={
                    "direction": decision_output.direction.value,
                    "confidence": decision_output.confidence,
                    "is_tradeable": decision_output.is_tradeable,
                },
            ))
        except Exception as e:
            logger.warning(f"Decision engine failed: {e}")
            stages.append(PipelineResult(
                stage=PipelineStage.MAKE_DECISION,
                status="failed", duration_ms=(time.time() - s7_start) * 1000, error=str(e),
            ))

        # ── Stage 8: Generate Signal (optional) ──
        signal_record = None
        if request.auto_generate_signal and decision_output and decision_output.is_tradeable:
            s8_start = time.time()
            try:
                from services.signals import SignalGenerator, save_signal
                signal_record = SignalGenerator.from_decision(
                    symbol=request.symbol,
                    timeframe=request.timeframe,
                    direction=decision_output.direction.value,
                    confidence=decision_output.confidence,
                    confluence_score=decision_output.deterministic.confluence_score if decision_output.deterministic else 0,
                    entry=decision_output.levels.entry,
                    stop_loss=decision_output.levels.stop_loss,
                    take_profit_1=decision_output.levels.take_profit_1,
                    take_profit_2=decision_output.levels.take_profit_2,
                    risk_reward_1=decision_output.levels.risk_reward_1,
                    risk_reward_2=decision_output.levels.risk_reward_2,
                    reasoning=decision_output.reasoning,
                    reasons=decision_output.reasons,
                    risks=decision_output.risks,
                )
                if signal_record:
                    save_signal(signal_record)
                stages.append(PipelineResult(
                    stage=PipelineStage.GENERATE_SIGNAL,
                    status="completed",
                    duration_ms=(time.time() - s8_start) * 1000,
                    data={"signal_id": signal_record.id if signal_record else None},
                ))
            except Exception as e:
                logger.warning(f"Signal generation failed: {e}")
                stages.append(PipelineResult(
                    stage=PipelineStage.GENERATE_SIGNAL,
                    status="failed", duration_ms=(time.time() - s8_start) * 1000, error=str(e),
                ))

        total_duration = (time.time() - start) * 1000

        return PipelineResponse(
            success=True,
            execution_id=exec_id,
            total_duration_ms=round(total_duration, 2),
            stages=stages,
            symbol=request.symbol,
            timeframe=request.timeframe,
            exchange=request.exchange,
            decision=decision_output.model_dump() if decision_output else None,
            signal=signal_record.model_dump() if signal_record else None,
        )
