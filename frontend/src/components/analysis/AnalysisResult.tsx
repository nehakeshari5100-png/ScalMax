'use client';

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import { GlassCard } from '@/components/ui/GlassCard';
import { ScoringGauge } from './ScoringGauge';
import { TradePlanPanel } from './TradePlanPanel';
import {
  TrendingUp, TrendingDown, Minus, Shield, Brain, Target,
  Zap, AlertTriangle, BarChart3, Eye, Activity, DollarSign,
} from 'lucide-react';
import type { ScoredTrade, VisionObservation } from '@/types/vision';

interface AnalysisResultProps {
  trade: ScoredTrade;
  observation: VisionObservation;
  model: string;
}

const SIGNAL_CONFIG: Record<string, { icon: any; color: string; bg: string; border: string; label: string }> = {
  STRONG_LONG: { icon: TrendingUp, color: 'text-aurora-400', bg: 'bg-aurora-500/15', border: 'border-aurora-500/25', label: 'STRONG LONG' },
  LONG: { icon: TrendingUp, color: 'text-aurora-500', bg: 'bg-aurora-500/10', border: 'border-aurora-500/15', label: 'LONG' },
  NEUTRAL: { icon: Minus, color: 'text-ember-400', bg: 'bg-ember-500/10', border: 'border-ember-500/20', label: 'NEUTRAL' },
  SHORT: { icon: TrendingDown, color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/15', label: 'SHORT' },
  STRONG_SHORT: { icon: TrendingDown, color: 'text-red-400', bg: 'bg-red-500/15', border: 'border-red-500/25', label: 'STRONG SHORT' },
};

function Tag({ children, color }: { children: string | number; color?: string }) {
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
  const isNoTrade = trade.signal === 'NEUTRAL' && trade.confidence === 0;
  const VerdictIcon = signal.icon;

  const confidenceColor = trade.confidence >= 80 ? 'bg-aurora-400' : trade.confidence >= 50 ? 'bg-ember-400' : 'bg-red-400';

  const obsTagColor = (v: string, bullish: string) => {
    if (v === bullish) return 'green';
    if (v === 'neutral' || v === 'none' || v === 'medium' || v === 'moderate' || v === 'ranging') return 'amber';
    return 'red';
  };

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-cyber-400" />
          <h2 className="text-base font-bold">Scored Trade</h2>
          <span className="text-[10px] text-[var(--color-text-muted)] font-mono">{model.split('/').pop()}</span>
        </div>
      </div>

      {/* Verdict */}
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
      </GlassCard>

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
            <span className="text-[10px] text-[var(--color-text-muted)]">AI Confidence</span>
            <Tag>{`${observation.confidence}%`}</Tag>
          </div>
        </div>
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
      {trade.confidence < 20 && (
        <GlassCard className="p-5 border border-ember-500/20">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-ember-400" />
            <p className="text-xs text-ember-400">Low confidence trade ({trade.confidence}%). Consider skipping or using a tighter stop.</p>
          </div>
          {observation.quality === 'UNREADABLE_CHART' && (
            <div className="flex items-center gap-2 mt-2">
              <AlertTriangle className="w-4 h-4 text-red-400" />
              <p className="text-xs text-red-400">Chart quality too low for reliable analysis.</p>
            </div>
          )}
        </GlassCard>
      )}

      {/* Trade Plan */}
      {trade.confidence >= 20 && (
        <TradePlanPanel analysis={{ entry_zone: trade.entry_zone, stop_loss: trade.stop_loss, take_profit_1: trade.take_profit_1, take_profit_2: trade.take_profit_2 }} />
      )}
    </motion.div>
  );
}
