'use client';

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import { GlassCard } from '@/components/ui/GlassCard';
import { ScoringGauge } from './ScoringGauge';
import { TradePlanPanel } from './TradePlanPanel';
import {
  TrendingUp, TrendingDown, Minus, Shield, Brain, Target,
  Zap,   AlertTriangle, BarChart3, Eye, Activity, DollarSign,
} from 'lucide-react';
import type { ScoredTrade, VisionObservation } from '@/types/vision';
import type { ReactNode } from 'react';

interface AnalysisResultProps {
  trade: ScoredTrade;
  observation: VisionObservation;
  model: string;
}

const SIGNAL_CONFIG: Record<string, { icon: any; color: string; bg: string; border: string; label: string }> = {
  STRONG_LONG: { icon: TrendingUp, color: 'text-aurora-400', bg: 'bg-aurora-500/15', border: 'border-aurora-500/25', label: 'STRONG LONG' },
  LONG: { icon: TrendingUp, color: 'text-aurora-500', bg: 'bg-aurora-500/10', border: 'border-aurora-500/15', label: 'LONG' },
  NEUTRAL: { icon: Minus, color: 'text-ember-400', bg: 'bg-ember-500/10', border: 'border-ember-500/20', label: 'NEUTRAL' },
  NO_TRADE: { icon: Minus, color: 'text-ember-400', bg: 'bg-ember-500/10', border: 'border-ember-500/20', label: 'NO TRADE' },
  SHORT: { icon: TrendingDown, color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/15', label: 'SHORT' },
  STRONG_SHORT: { icon: TrendingDown, color: 'text-red-400', bg: 'bg-red-500/15', border: 'border-red-500/25', label: 'STRONG SHORT' },
};

function Tag({ children, color }: { children: ReactNode; color?: string }) {
  return (
    <span className={cn(
      'inline-flex px-2 py-0.5 rounded text-[10px] font-medium',
      color === 'green' && 'bg-aurora-500/10 text-aurora-400',
      color === 'red' && 'bg-red-500/10 text-red-400',
      color === 'amber' && 'bg-ember-500/10 text-ember-400',
      color === 'blue' && 'bg-cyber-500/10 text-cyber-400',
      !color && 'bg-surface-elevated/60 text-[var(--color-text-muted)]',
    )}>{children}</span>
  );
}

export function AnalysisResult({ trade, observation, model }: AnalysisResultProps) {
  const signal = SIGNAL_CONFIG[trade.signal] || SIGNAL_CONFIG.NEUTRAL;
  const isNoTrade = trade.signal === 'NO_TRADE' || (trade.signal === 'NEUTRAL' && trade.confidence === 0);
  const VerdictIcon = signal.icon;

  const confidenceColor = trade.confidence >= 85 ? 'bg-aurora-400' : trade.confidence >= 70 ? 'bg-cyber-400' : trade.confidence >= 50 ? 'bg-ember-400' : 'bg-red-400';

  const obsTagColor = (v: string, bullish: string) => {
    if (v === bullish) return 'green';
    if (v === 'neutral' || v === 'none' || v === 'medium' || v === 'moderate' || v === 'ranging') return 'amber';
    return 'red';
  };

  const ld = observation.liquidityDetails;
  const liqIndicators = [
    ld?.equalHighs && 'Equal Highs',
    ld?.equalLows && 'Equal Lows',
    ld?.liquiditySweeps && 'Sweep',
    ld?.stopHunts && 'Stop Hunt',
  ].filter((x): x is string => Boolean(x));

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-cyber-400" />
          <h2 className="text-base font-bold">Scored Trade</h2>
          <span className="text-[10px] text-[var(--color-text-muted)] font-mono">{model.split('/').pop()}</span>
        </div>
      </div>

      <GlassCard className={cn('p-6 border', signal.border)}>
        <div className="flex items-center gap-4">
          <div className={cn('w-14 h-14 rounded-2xl flex items-center justify-center', signal.bg)}>
            <VerdictIcon className={cn('w-7 h-7', signal.color)} />
          </div>
          <div className="flex-1">
            <p className={cn('text-lg font-bold', signal.color)}>
              {isNoTrade ? 'NO TRADE' : signal.label}
            </p>
            <p className="text-xs text-[var(--color-text-muted)] mt-0.5">Engine Decision</p>
            <p className="text-[10px] text-[var(--color-text-muted)] mt-0.5">
              Bull {trade.bullScore} / Bear {trade.bearScore}
            </p>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-2">
              <div className="w-20 h-2 rounded-full bg-white/5 overflow-hidden">
                <div className={cn('h-full rounded-full transition-all', confidenceColor)} style={{ width: `${trade.confidence}%` }} />
              </div>
              <span className={cn('text-sm font-bold font-mono', confidenceColor.replace('bg-', 'text-'))}>{trade.confidence}%</span>
            </div>
            <p className="text-[10px] text-[var(--color-text-muted)] mt-0.5">Engine Confidence</p>
          </div>
        </div>

        {/* Risk Summary */}
        {trade.riskSummary && (
          <div className="mt-4 pt-3 border-t border-white/5 flex items-start gap-2">
            <AlertTriangle className="w-3.5 h-3.5 text-cyber-400 mt-0.5 shrink-0" />
            <p className="text-[11px] text-[var(--color-text-muted)]">{trade.riskSummary}</p>
          </div>
        )}
      </GlassCard>

      {/* PHASE 6: Visual Debug — Detected Chart Info */}
      {(observation.detectedSymbol || observation.detectedTimeframe || observation.detectedCurrentPrice || observation.ocrConfidence > 0) && (
        <GlassCard className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <Eye className="w-4 h-4 text-cyber-400" />
            <h3 className="text-sm font-semibold">Detected Chart Info</h3>
            {observation.ocrConfidence > 0 && (
              <Tag color={observation.ocrConfidence >= 80 ? 'green' : 'red'}>{`OCR ${observation.ocrConfidence}%`}</Tag>
            )}
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-4 gap-y-2">
            {observation.detectedSymbol && (
              <div>
                <span className="text-[10px] text-[var(--color-text-muted)]">Symbol</span>
                <p className="text-xs font-mono font-medium">{observation.detectedSymbol}</p>
              </div>
            )}
            {observation.detectedTimeframe && (
              <div>
                <span className="text-[10px] text-[var(--color-text-muted)]">Timeframe</span>
                <p className="text-xs font-mono font-medium">{observation.detectedTimeframe}</p>
              </div>
            )}
            {observation.detectedExchange && (
              <div>
                <span className="text-[10px] text-[var(--color-text-muted)]">Exchange</span>
                <p className="text-xs font-mono font-medium">{observation.detectedExchange}</p>
              </div>
            )}
            {observation.detectedCurrentPrice && (
              <div>
                <span className="text-[10px] text-[var(--color-text-muted)]">Current Price</span>
                <p className="text-xs font-mono font-medium text-aurora-400">{observation.detectedCurrentPrice}</p>
              </div>
            )}
            {observation.detectedIndicatorNames && (
              <div>
                <span className="text-[10px] text-[var(--color-text-muted)]">Indicators</span>
                <p className="text-xs font-mono font-medium">{observation.detectedIndicatorNames}</p>
              </div>
            )}
          </div>
          {(observation.isHigherHighs !== null || observation.isHigherLows !== null) && (
            <div className="mt-3 pt-3 border-t border-white/5 flex flex-wrap gap-1.5">
              {observation.isHigherHighs !== null && (
                <Tag color={observation.isHigherHighs ? 'green' : 'amber'}>HH:{observation.isHigherHighs ? 'YES' : 'NO'}</Tag>
              )}
              {observation.isHigherLows !== null && (
                <Tag color={observation.isHigherLows ? 'green' : 'amber'}>HL:{observation.isHigherLows ? 'YES' : 'NO'}</Tag>
              )}
              {observation.isLowerHighs !== null && (
                <Tag color={observation.isLowerHighs ? 'red' : 'amber'}>LH:{observation.isLowerHighs ? 'YES' : 'NO'}</Tag>
              )}
              {observation.isLowerLows !== null && (
                <Tag color={observation.isLowerLows ? 'red' : 'amber'}>LL:{observation.isLowerLows ? 'YES' : 'NO'}</Tag>
              )}
            </div>
          )}
        </GlassCard>
      )}

      {/* Reasoning */}
      {(trade.reason || observation.reason || observation.observedTrend) && (
        <GlassCard className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <Brain className="w-4 h-4 text-cyber-400" />
            <h3 className="text-sm font-semibold">Reasoning</h3>
          </div>
          {trade.reason && (
            <p className="text-[11px] text-[var(--color-text-muted)] leading-relaxed">{trade.reason}</p>
          )}
          {!trade.reason && observation.reason && (
            <p className="text-[11px] text-[var(--color-text-muted)] leading-relaxed">{observation.reason}</p>
          )}
          <div className="mt-3 grid grid-cols-1 gap-2">
            {observation.observedTrend && (
              <div className="flex items-start gap-2">
                <TrendingUp className="w-3 h-3 text-aurora-400 mt-0.5 shrink-0" />
                <div>
                  <span className="text-[10px] font-medium text-[var(--color-text-muted)]">Observed Trend</span>
                  <p className="text-[11px] text-[var(--color-text-muted)]">{observation.observedTrend}</p>
                </div>
              </div>
            )}
            {observation.observedStructure && (
              <div className="flex items-start gap-2">
                <BarChart3 className="w-3 h-3 text-cyber-400 mt-0.5 shrink-0" />
                <div>
                  <span className="text-[10px] font-medium text-[var(--color-text-muted)]">Observed Structure</span>
                  <p className="text-[11px] text-[var(--color-text-muted)]">{observation.observedStructure}</p>
                </div>
              </div>
            )}
            {observation.observedMomentum && (
              <div className="flex items-start gap-2">
                <Zap className="w-3 h-3 text-amber-400 mt-0.5 shrink-0" />
                <div>
                  <span className="text-[10px] font-medium text-[var(--color-text-muted)]">Observed Momentum</span>
                  <p className="text-[11px] text-[var(--color-text-muted)]">{observation.observedMomentum}</p>
                </div>
              </div>
            )}
            {observation.observedSupport && (
              <div className="flex items-start gap-2">
                <Shield className="w-3 h-3 text-aurora-400 mt-0.5 shrink-0" />
                <div>
                  <span className="text-[10px] font-medium text-[var(--color-text-muted)]">Observed Support</span>
                  <p className="text-[11px] text-[var(--color-text-muted)]">{observation.observedSupport}</p>
                </div>
              </div>
            )}
            {observation.observedResistance && (
              <div className="flex items-start gap-2">
                <TrendingDown className="w-3 h-3 text-red-400 mt-0.5 shrink-0" />
                <div>
                  <span className="text-[10px] font-medium text-[var(--color-text-muted)]">Observed Resistance</span>
                  <p className="text-[11px] text-[var(--color-text-muted)]">{observation.observedResistance}</p>
                </div>
              </div>
            )}
          </div>
        </GlassCard>
      )}

      {/* Observations */}
      <GlassCard className="p-4">
        <div className="flex items-center gap-2 mb-3">
          <Activity className="w-4 h-4 text-cyber-400" />
          <h3 className="text-sm font-semibold">Chart Observations</h3>
        </div>
        <div className="flex flex-wrap gap-2">
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] text-[var(--color-text-muted)]">Trend</span>
            <Tag color={obsTagColor(observation.trend, 'bullish')}>{observation.trend}</Tag>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] text-[var(--color-text-muted)]">Structure</span>
            <Tag color={obsTagColor(observation.marketStructure, 'HH_HL')}>{observation.marketStructure}</Tag>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] text-[var(--color-text-muted)]">Momentum</span>
            <Tag color={obsTagColor(observation.momentum, 'strong')}>{observation.momentum}</Tag>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] text-[var(--color-text-muted)]">Liquidity</span>
            <Tag color={obsTagColor(observation.liquidity, 'below_lows')}>{observation.liquidity}</Tag>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] text-[var(--color-text-muted)]">Volume</span>
            <Tag color={obsTagColor(observation.volume, 'high')}>{observation.volume}</Tag>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] text-[var(--color-text-muted)]">Confluence</span>
            <Tag color={obsTagColor(observation.confluence || 'none', 'support')}>{observation.confluence || 'none'}</Tag>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] text-[var(--color-text-muted)]">AI Confidence</span>
            <Tag>{`${observation.confidence}%`}</Tag>
          </div>
        </div>

        {/* Liquidity Details */}
        {liqIndicators.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {liqIndicators.map((indicator) => (
              <Tag key={indicator} color="blue">{indicator}</Tag>
            ))}
          </div>
        )}

        {/* Market Structure Summary */}
        {trade.marketStructureSummary && (
          <div className="mt-3 pt-3 border-t border-white/5">
            <div className="flex items-center gap-1.5 mb-1">
              <BarChart3 className="w-3 h-3 text-cyber-400" />
              <span className="text-[10px] font-medium text-[var(--color-text-muted)]">Market Structure</span>
            </div>
            <p className="text-[11px] text-[var(--color-text-muted)]">{trade.marketStructureSummary}</p>
          </div>
        )}

        {/* Liquidity Summary */}
        {trade.liquiditySummary && (
          <div className="mt-2">
            <div className="flex items-center gap-1.5 mb-1">
              <Eye className="w-3 h-3 text-cyber-400" />
              <span className="text-[10px] font-medium text-[var(--color-text-muted)]">Liquidity</span>
            </div>
            <p className="text-[11px] text-[var(--color-text-muted)]">{trade.liquiditySummary}</p>
          </div>
        )}
      </GlassCard>

      {/* Scoring */}
      <ScoringGauge scoring={trade.scoring} />

      {/* Trade Setup */}
      <GlassCard className="p-5">
        <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/5">
          <Target className="w-4 h-4 text-aurora-400" />
          <h3 className="text-sm font-semibold">Trade Setup</h3>
        </div>
        <div className="grid grid-cols-2 gap-x-6 gap-y-3">
          <div><span className="text-xs text-[var(--color-text-muted)]">Entry Zone</span><p className="font-mono text-sm font-medium">{trade.entry_zone || '-'}</p></div>
          <div><span className="text-xs text-[var(--color-text-muted)]">Stop Loss</span><p className="font-mono text-sm font-medium text-red-400">{trade.stop_loss || '-'}</p></div>
          <div><span className="text-xs text-[var(--color-text-muted)]">TP 1</span><p className="font-mono text-sm font-medium text-aurora-400">{trade.take_profit_1 || '-'}</p></div>
          <div><span className="text-xs text-[var(--color-text-muted)]">TP 2</span><p className="font-mono text-sm font-medium text-aurora-400">{trade.take_profit_2 || '-'}</p></div>
          <div className="col-span-2"><span className="text-xs text-[var(--color-text-muted)]">Risk/Reward</span><p className="font-mono text-sm font-medium">{trade.risk_reward || '-'}</p></div>
        </div>
      </GlassCard>

      {/* Risk Assessment */}
      {(trade.confidence < 50 || observation.ocrConfidence < 80) && (
        <GlassCard className="p-5 border border-ember-500/20">
          {observation.ocrConfidence < 80 && observation.ocrConfidence > 0 && (
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-ember-400" />
              <p className="text-xs text-ember-400">Low OCR confidence ({observation.ocrConfidence}%). Chart details may be unreliable.</p>
            </div>
          )}
          {trade.confidence < 50 && trade.confidence > 0 && (
            <div className={cn("flex items-center gap-2", observation.ocrConfidence < 80 ? "mt-2" : "")}>
              <AlertTriangle className="w-4 h-4 text-ember-400" />
              <p className="text-xs text-ember-400">Low confidence trade ({trade.confidence}%). Consider skipping or using a tighter stop.</p>
            </div>
          )}
          {observation.quality === 'UNREADABLE_CHART' && (
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-red-400" />
              <p className="text-xs text-red-400">Chart quality too low for reliable analysis.</p>
            </div>
          )}
        </GlassCard>
      )}

      {/* Trade Plan */}
      {trade.confidence >= 50 && trade.signal !== 'NO_TRADE' && (
        <TradePlanPanel analysis={{ entry_zone: trade.entry_zone, stop_loss: trade.stop_loss, take_profit_1: trade.take_profit_1, take_profit_2: trade.take_profit_2 }} />
      )}
    </motion.div>
  );
}
