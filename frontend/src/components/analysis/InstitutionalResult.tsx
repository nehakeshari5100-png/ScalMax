'use client';

import { motion } from 'framer-motion';
import { memo } from 'react';
import { cn } from '@/lib/utils';
import { GlassCard } from '@/components/ui/GlassCard';
import {
  TrendingUp, TrendingDown, Minus, Shield, Target,
  Zap, BarChart3, Eye, Activity, AlertTriangle, CheckCircle,
} from 'lucide-react';
import type { MarketExtraction, InstitutionalDecision } from '@/types/vision';

interface Props {
  extraction: MarketExtraction;
  inst: InstitutionalDecision;
  model: string;
}

const MARKET_STATE_ICONS: Record<string, any> = {
  TRENDING: TrendingUp,
  RANGING: Minus,
  BREAKOUT: Zap,
  RETEST: Activity,
  LIQUIDITY_SWEEP: Eye,
  REVERSAL: TrendingDown,
};

const GRADE_CONFIG: Record<string, { color: string; bg: string }> = {
  'A+': { color: 'text-aurora-400', bg: 'bg-aurora-500/10' },
  'A': { color: 'text-aurora-400', bg: 'bg-aurora-500/10' },
  'B': { color: 'text-cyber-400', bg: 'bg-cyber-500/10' },
  'C': { color: 'text-ember-400', bg: 'bg-ember-500/10' },
  'D': { color: 'text-red-400', bg: 'bg-red-500/10' },
};

const BIAS_CONFIG: Record<string, { icon: any; color: string; bg: string; label: string }> = {
  STRONG_LONG: { icon: TrendingUp, color: 'text-aurora-400', bg: 'bg-aurora-500/15', label: 'STRONG LONG' },
  LONG: { icon: TrendingUp, color: 'text-aurora-400', bg: 'bg-aurora-500/10', label: 'LONG' },
  NEUTRAL: { icon: Minus, color: 'text-ember-400', bg: 'bg-ember-500/10', label: 'NEUTRAL' },
  SHORT: { icon: TrendingDown, color: 'text-red-400', bg: 'bg-red-500/10', label: 'SHORT' },
  STRONG_SHORT: { icon: TrendingDown, color: 'text-red-400', bg: 'bg-red-500/15', label: 'STRONG SHORT' },
  NO_TRADE: { icon: Minus, color: 'text-ember-400', bg: 'bg-ember-500/10', label: 'NO TRADE' },
};

const TRADE_ICONS: Record<string, any> = {
  LONG: TrendingUp,
  SHORT: TrendingDown,
  NO_TRADE: Minus,
};

const STATE_LABELS: Record<string, string> = {
  TRENDING: 'Trending',
  RANGING: 'Ranging',
  BREAKOUT: 'Breakout',
  RETEST: 'Retest',
  LIQUIDITY_SWEEP: 'Liquidity Sweep',
  REVERSAL: 'Reversal',
};

export const InstitutionalResult = memo(function InstitutionalResult({ extraction: { chartDetection: cd }, inst, model }: Props) {
  const biasCfg = BIAS_CONFIG[inst.bias] || BIAS_CONFIG.NO_TRADE;
  const BiasIcon = biasCfg.icon;
  const gradeCfg = GRADE_CONFIG[inst.tradeGrade] || { color: 'text-[var(--color-text-muted)]', bg: 'bg-white/5' };
  const tradeBiasCfg = BIAS_CONFIG[inst.tradePlan?.bias] || BIAS_CONFIG.NO_TRADE;
  const TradeIcon = tradeBiasCfg.icon;
  const StateIcon = MARKET_STATE_ICONS[inst.marketState] || Activity;
  const grade = inst.tradeGrade || '-';

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-cyber-400" />
          <h2 className="text-base font-bold">Institutional Trade Decision</h2>
          <span className="text-[10px] text-[var(--color-text-muted)] font-mono">{model.split('/').pop()}</span>
        </div>
      </div>

      {/* Verdict */}
      <GlassCard className={cn('p-5 border', biasCfg.bg.replace('/10', '/5').replace('/15', '/5'))}>
        <div className="flex items-center gap-4">
          <div className={cn('w-14 h-14 rounded-2xl flex items-center justify-center', biasCfg.bg)}>
            <BiasIcon className={cn('w-7 h-7', biasCfg.color)} />
          </div>
          <div className="flex-1">
            <p className={cn('text-lg font-bold', biasCfg.color)}>{biasCfg.label}</p>
            <p className="text-xs text-[var(--color-text-muted)] mt-0.5">Bias</p>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-2">
              <span className={cn('text-lg font-bold font-mono', gradeCfg.color)}>{grade}</span>
              <span className="text-[10px] text-[var(--color-text-muted)]">Grade</span>
            </div>
            {inst.tradePlan?.confidence > 0 && (
              <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
                Conf: {inst.tradePlan.confidence}%
              </p>
            )}
          </div>
        </div>
      </GlassCard>

      {/* STEP 1 - Market State */}
      <GlassCard className="p-4">
        <div className="flex items-center gap-2 mb-3">
          <StateIcon className="w-4 h-4 text-cyber-400" />
          <h3 className="text-sm font-semibold">Market State</h3>
          <span className={cn(
            'text-xs font-bold',
            ['TRENDING', 'BREAKOUT'].includes(inst.marketState) ? 'text-aurora-400' :
            inst.marketState === 'RANGING' ? 'text-ember-400' :
            inst.marketState === 'REVERSAL' ? 'text-red-400' : 'text-cyber-400'
          )}>{STATE_LABELS[inst.marketState] || inst.marketState}</span>
        </div>
        {cd.symbol && <div className="text-[11px] text-[var(--color-text-muted)]"><span className="text-[10px] font-medium">Symbol: </span>{cd.symbol} {cd.timeframe && `(${cd.timeframe})`}</div>}
        {cd.currentPrice && <div className="text-[11px] text-[var(--color-text-muted)]"><span className="text-[10px] font-medium">Price: </span>{cd.currentPrice}</div>}
      </GlassCard>

      {/* STEP 5 - Trade Grade */}
      <GlassCard className="p-4">
        <div className="flex items-center gap-2 mb-3">
          <Shield className="w-4 h-4 text-cyber-400" />
          <h3 className="text-sm font-semibold">Trade Quality</h3>
          <span className={cn('text-sm font-bold font-mono', gradeCfg.color)}>{grade}</span>
        </div>
        <div className="flex items-center gap-2">
          {inst.riskReward && <span className="text-xs text-[var(--color-text-muted)]">RR: {inst.riskReward}</span>}
          {inst.probabilityScore && <span className="text-xs text-[var(--color-text-muted)]">| P: {inst.probabilityScore}%</span>}
        </div>
      </GlassCard>

      {/* STEP 2 - Directional Bias Details */}
      <GlassCard className="p-4">
        <div className="flex items-center gap-2 mb-3">
          <Eye className="w-4 h-4 text-cyber-400" />
          <h3 className="text-sm font-semibold">Directional Bias</h3>
        </div>
        <div className="flex items-center gap-3">
          <div className={cn('px-3 py-1.5 rounded-lg flex items-center gap-2', biasCfg.bg)}>
            <BiasIcon className={cn('w-4 h-4', biasCfg.color)} />
            <span className={cn('text-sm font-semibold', biasCfg.color)}>{biasCfg.label}</span>
          </div>
        </div>
      </GlassCard>

      {/* STEP 6 - Conflict Detection */}
      {inst.conflictReport && (inst.conflictReport.bullishFactors.length > 0 || inst.conflictReport.bearishFactors.length > 0) && (
        <GlassCard className="p-4">
          <div className="flex items-center gap-2 mb-3">
            {inst.conflictReport.highConflict ? <AlertTriangle className="w-4 h-4 text-ember-400" /> : <CheckCircle className="w-4 h-4 text-aurora-400" />}
            <h3 className="text-sm font-semibold">Conflict Detection</h3>
            {inst.conflictReport.highConflict && <span className="text-[10px] text-ember-400 font-medium">HIGH CONFLICT</span>}
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <p className="text-[10px] font-medium text-aurora-400 mb-1">Bullish Factors</p>
              <ul className="space-y-0.5">
                {inst.conflictReport.bullishFactors.map((f, i) => (
                  <li key={i} className="text-[11px] text-[var(--color-text-muted)] pl-2 border-l-2 border-aurora-500/30">{f}</li>
                ))}
              </ul>
            </div>
            <div>
              <p className="text-[10px] font-medium text-red-400 mb-1">Bearish Factors</p>
              <ul className="space-y-0.5">
                {inst.conflictReport.bearishFactors.map((f, i) => (
                  <li key={i} className="text-[11px] text-[var(--color-text-muted)] pl-2 border-l-2 border-red-500/30">{f}</li>
                ))}
              </ul>
            </div>
          </div>
        </GlassCard>
      )}

      {/* STEP 3 + 7 + 8 - Trade Plan + Liquidity Target + Execution */}
      {inst.tradePlan?.entry && inst.tradePlan?.bias !== 'NO_TRADE' && (
        <>
          {/* Trade Plan */}
          <GlassCard className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <Target className="w-4 h-4 text-aurora-400" />
              <h3 className="text-sm font-semibold">Trade Plan</h3>
              {inst.riskReward && <span className="text-[10px] font-mono text-aurora-400 ml-auto">RR {inst.riskReward}</span>}
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3">
              <div className="min-w-0"><span className="text-xs text-[var(--color-text-muted)]">Entry</span><p className="font-mono text-sm font-medium break-all">{inst.tradePlan.entry}</p></div>
              <div className="min-w-0"><span className="text-xs text-[var(--color-text-muted)]">Stop</span><p className="font-mono text-sm font-medium text-red-400 break-all">{inst.tradePlan.stop}</p></div>
              {inst.tradePlan.tp1 && <div className="min-w-0"><span className="text-xs text-[var(--color-text-muted)]">TP1</span><p className="font-mono text-sm font-medium text-aurora-400 break-all">{inst.tradePlan.tp1}</p></div>}
              {inst.tradePlan.tp2 && <div className="min-w-0"><span className="text-xs text-[var(--color-text-muted)]">TP2</span><p className="font-mono text-sm font-medium text-aurora-400 break-all">{inst.tradePlan.tp2}</p></div>}
              {inst.tradePlan.tp3 && <div className="min-w-0"><span className="text-xs text-[var(--color-text-muted)]">TP3</span><p className="font-mono text-sm font-medium text-aurora-400 break-all">{inst.tradePlan.tp3}</p></div>}
            </div>
          </GlassCard>

          {/* Liquidity Target */}
          {inst.liquidityTarget && (inst.liquidityTarget.nearest || inst.liquidityTarget.major) && (
            <GlassCard className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <Eye className="w-4 h-4 text-cyber-400" />
                <h3 className="text-sm font-semibold">Liquidity Target</h3>
              </div>
              <div className="space-y-1 text-[11px] text-[var(--color-text-muted)]">
                {inst.liquidityTarget.nearest && <div><span className="text-[10px] font-medium">Nearest: </span>{inst.liquidityTarget.nearest}</div>}
                {inst.liquidityTarget.major && <div><span className="text-[10px] font-medium">Major: </span>{inst.liquidityTarget.major}</div>}
                {inst.liquidityTarget.final && <div><span className="text-[10px] font-medium">Final: </span>{inst.liquidityTarget.final}</div>}
              </div>
            </GlassCard>
          )}

          {/* Execution Plan */}
          {inst.executionPlan && (inst.executionPlan.entryTrigger || inst.executionPlan.invalidation) && (
            <GlassCard className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <Activity className="w-4 h-4 text-cyber-400" />
                <h3 className="text-sm font-semibold">Execution Plan</h3>
              </div>
              <div className="space-y-2 text-[11px] text-[var(--color-text-muted)]">
                {inst.executionPlan.entryTrigger && <div><span className="text-[10px] font-medium text-aurora-400">Entry Trigger: </span>{inst.executionPlan.entryTrigger}</div>}
                {inst.executionPlan.invalidation && <div><span className="text-[10px] font-medium text-red-400">Invalidation: </span>{inst.executionPlan.invalidation}</div>}
                {inst.executionPlan.targetLogic && <div><span className="text-[10px] font-medium text-cyber-400">Target Logic: </span>{inst.executionPlan.targetLogic}</div>}
              </div>
            </GlassCard>
          )}
        </>
      )}

      {/* STEP 10 - Confidence Engine */}
      {inst.confidence && inst.confidence.total > 0 && (
        <GlassCard className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <BarChart3 className="w-4 h-4 text-cyber-400" />
            <h3 className="text-sm font-semibold">Confidence Engine</h3>
            <span className={cn(
              'text-sm font-bold font-mono ml-auto',
              inst.confidence.total >= 80 ? 'text-aurora-400' : inst.confidence.total >= 60 ? 'text-cyber-400' : 'text-ember-400'
            )}>{inst.confidence.total}/100</span>
          </div>
          <div className="space-y-2">
            {[
              { label: 'Structure', value: inst.confidence.structure, weight: '25%' },
              { label: 'Liquidity', value: inst.confidence.liquidity, weight: '20%' },
              { label: 'SMC', value: inst.confidence.smc, weight: '20%' },
              { label: 'Volume', value: inst.confidence.volume, weight: '15%' },
              { label: 'Momentum', value: inst.confidence.momentum, weight: '10%' },
              { label: 'RR', value: inst.confidence.rr, weight: '10%' },
            ].map((item) => (
              <div key={item.label} className="flex items-center gap-3">
                <span className="text-[10px] text-[var(--color-text-muted)] w-20 shrink-0">{item.label} <span className="text-[9px]">({item.weight})</span></span>
                <div className="flex-1 h-1.5 rounded-full bg-white/5 overflow-hidden">
                  <div className="h-full rounded-full bg-cyber-400" style={{ width: `${item.value}%` }} />
                </div>
                <span className="text-[10px] font-mono text-[var(--color-text-muted)] w-8 text-right">{item.value}</span>
              </div>
            ))}
          </div>
        </GlassCard>
      )}

      {/* Reasoning */}
      {inst.reasoning && inst.reasoning.length > 0 && (
        <GlassCard className="p-4">
          <div className="flex items-center gap-2 mb-2">
            <Activity className="w-4 h-4 text-cyber-400" />
            <h3 className="text-sm font-semibold">Reasoning</h3>
          </div>
          <ul className="space-y-1">
            {inst.reasoning.map((r, i) => (
              <li key={i} className="text-[11px] text-[var(--color-text-muted)] pl-3 border-l-2 border-cyber-500/30">{r}</li>
            ))}
          </ul>
        </GlassCard>
      )}
    </motion.div>
  );
});
