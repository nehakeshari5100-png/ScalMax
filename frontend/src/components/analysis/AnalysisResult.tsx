'use client';

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import { GlassCard } from '@/components/ui/GlassCard';
import { Badge } from '@/components/ui/Badge';
import {
  TrendingUp, TrendingDown, Minus, Shield, Brain, Target,
  Zap, AlertTriangle, BarChart3, Eye,
} from 'lucide-react';
import type { ChartAnalysisResult } from '@/types/vision';

interface AnalysisResultProps {
  data: ChartAnalysisResult;
  model: string;
}

function Section({ title, icon: Icon, children, className }: { title: string; icon: any; children: React.ReactNode; className?: string }) {
  return (
    <GlassCard className={cn('p-5', className)}>
      <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/5">
        <Icon className="w-4 h-4 text-aurora-400" />
        <h3 className="text-sm font-semibold">{title}</h3>
      </div>
      <div className="space-y-2 text-sm leading-relaxed text-[var(--color-text)]">
        {children}
      </div>
    </GlassCard>
  );
}

function Tag({ children, variant }: { children: string; variant?: 'info' | 'success' | 'warn' | 'default' }) {
  return (
    <span className={cn(
      'inline-flex px-2.5 py-1 rounded-md text-xs font-medium',
      variant === 'info' && 'bg-cyber-500/10 text-cyber-400 border border-cyber-500/20',
      variant === 'success' && 'bg-aurora-500/10 text-aurora-400 border border-aurora-500/20',
      variant === 'warn' && 'bg-ember-500/10 text-ember-400 border border-ember-500/20',
      variant === 'default' && 'bg-surface-elevated/60 text-[var(--color-text-muted)] border border-white/5',
    )}>{children}</span>
  );
}

export function AnalysisResult({ data, model }: AnalysisResultProps) {
  const isLong = data.direction === 'LONG';
  const isShort = data.direction === 'SHORT';
  const isNoTrade = data.direction === 'NO_TRADE';

  const VerdictIcon = isLong ? TrendingUp : isShort ? TrendingDown : Minus;
  const verdictColor = isLong ? 'text-aurora-400' : isShort ? 'text-red-400' : 'text-ember-400';
  const verdictBg = isLong ? 'bg-aurora-500/10' : isShort ? 'bg-red-500/10' : 'bg-ember-500/10';
  const verdictBorder = isLong ? 'border-aurora-500/20' : isShort ? 'border-red-500/20' : 'border-ember-500/20';

  const confidenceColor = data.confidence >= 80 ? 'bg-aurora-400' : data.confidence >= 50 ? 'bg-ember-400' : 'bg-red-400';

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-cyber-400" />
          <h2 className="text-base font-bold">Analysis Results</h2>
          <span className="text-[10px] text-[var(--color-text-muted)] font-mono">{model.split('/').pop()}</span>
        </div>
      </div>

      {/* AI Verdict */}
      <GlassCard className={cn('p-6 border', verdictBorder)}>
        <div className="flex items-center gap-4">
          <div className={cn('w-14 h-14 rounded-2xl flex items-center justify-center', verdictBg)}>
            <VerdictIcon className={cn('w-7 h-7', verdictColor)} />
          </div>
          <div className="flex-1">
            <p className={cn('text-lg font-bold', verdictColor)}>
              {isNoTrade ? 'NO TRADE' : data.direction}
            </p>
            <p className="text-xs text-[var(--color-text-muted)] mt-0.5">AI Verdict</p>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-2">
              <div className="w-20 h-2 rounded-full bg-white/5 overflow-hidden">
                <div className={cn('h-full rounded-full transition-all', confidenceColor)} style={{ width: `${data.confidence}%` }} />
              </div>
              <span className={cn('text-sm font-bold font-mono', confidenceColor.replace('bg-', 'text-'))}>{data.confidence}%</span>
            </div>
            <p className="text-[10px] text-[var(--color-text-muted)] mt-0.5">Confidence</p>
          </div>
        </div>
      </GlassCard>

      <div className="grid lg:grid-cols-2 gap-5">
        {/* Trade Setup */}
        <Section title="Trade Setup" icon={Target}>
          <div className="grid grid-cols-2 gap-x-6 gap-y-3">
            <div><span className="text-xs text-[var(--color-text-muted)]">Entry Zone</span><p className="font-mono text-sm font-medium">{data.entry_zone || '-'}</p></div>
            <div><span className="text-xs text-[var(--color-text-muted)]">Stop Loss</span><p className="font-mono text-sm font-medium text-red-400">{data.invalidation || '-'}</p></div>
            <div><span className="text-xs text-[var(--color-text-muted)]">Take Profit 1</span><p className="font-mono text-sm font-medium text-aurora-400">{data.target_1 || '-'}</p></div>
            <div><span className="text-xs text-[var(--color-text-muted)]">Take Profit 2</span><p className="font-mono text-sm font-medium text-aurora-400">{data.target_2 || '-'}</p></div>
            <div className="col-span-2"><span className="text-xs text-[var(--color-text-muted)]">Risk/Reward</span><p className="font-mono text-sm font-medium">{data.risk_reward || '-'}</p></div>
          </div>
          {data.reasons.length > 0 && (
            <div className="mt-4 pt-4 border-t border-white/5">
              <span className="text-xs text-[var(--color-text-muted)] block mb-2">Reasons</span>
              <ul className="space-y-1">
                {data.reasons.map((r, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs text-[var(--color-text)]">
                    <span className="text-aurora-400 mt-0.5">&#x2022;</span>
                    {r}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </Section>

        {/* Risk Assessment */}
        <Section title="Risk Assessment" icon={AlertTriangle}>
          {data.warnings.length > 0 ? (
            <ul className="space-y-2">
              {data.warnings.map((w, i) => (
                <li key={i} className="flex items-start gap-2 text-sm px-3 py-2 rounded-lg bg-ember-500/5 border border-ember-500/10">
                  <AlertTriangle className="w-4 h-4 text-ember-400 shrink-0 mt-0.5" />
                  <span className="text-xs text-ember-400/90">{w}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-[var(--color-text-muted)]">No warnings detected</p>
          )}
          {data.riskZones.length > 0 && (
            <div className="mt-4">
              <span className="text-xs text-[var(--color-text-muted)] block mb-2">Risk Zones</span>
              <ul className="space-y-1">
                {data.riskZones.map((z, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs text-[var(--color-text)]">
                    <span className="text-red-400 mt-0.5">&#x2022;</span>
                    {z}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </Section>

        {/* Market Structure */}
        <Section title="Market Structure" icon={BarChart3}>
          <div className="space-y-3">
            <div>
              <span className="text-xs text-[var(--color-text-muted)]">Trend</span>
              <p className="text-sm mt-0.5">{data.trend || 'Not available'}</p>
            </div>
            <div>
              <span className="text-xs text-[var(--color-text-muted)]">Structure</span>
              <p className="text-sm mt-0.5">{data.marketStructure || 'Not available'}</p>
            </div>
            <div>
              <span className="text-xs text-[var(--color-text-muted)]">Trend Strength</span>
              <p className="text-sm mt-0.5">{data.trendStrength || 'Not available'}</p>
            </div>
          </div>
        </Section>

        {/* Liquidity Analysis */}
        <Section title="Liquidity Analysis" icon={Eye}>
          <p className="text-sm">{data.liquidity || 'Not available'}</p>
        </Section>

        {/* SMC Analysis */}
        <Section title="Smart Money Concepts" icon={Eye} className="lg:col-span-2">
          <div className="grid sm:grid-cols-2 gap-4">
            <div className="space-y-3">
              <div className="flex items-start gap-3 p-3 rounded-lg bg-surface-elevated/40 border border-white/5">
                <div className="w-4 h-4 text-cyber-400 shrink-0 mt-0.5 flex items-center justify-center"><span className="text-xs font-bold">&#x2194;</span></div>
                <div>
                  <span className="text-xs font-medium text-cyber-400">FVG</span>
                  <p className="text-xs mt-1 text-[var(--color-text)]">{data.fvg || 'Not detected'}</p>
                </div>
              </div>
              <div className="flex items-start gap-3 p-3 rounded-lg bg-surface-elevated/40 border border-white/5">
                <Shield className="w-4 h-4 text-aurora-400 shrink-0 mt-0.5" />
                <div>
                  <span className="text-xs font-medium text-aurora-400">Order Blocks</span>
                  <p className="text-xs mt-1 text-[var(--color-text)]">{data.orderBlocks || 'Not detected'}</p>
                </div>
              </div>
            </div>
            <div className="space-y-3">
              <div className="flex items-start gap-3 p-3 rounded-lg bg-surface-elevated/40 border border-white/5">
                <Zap className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
                <div>
                  <span className="text-xs font-medium text-purple-400">Break of Structure</span>
                  <p className="text-xs mt-1 text-[var(--color-text)]">{data.bos || 'Not detected'}</p>
                </div>
              </div>
              <div className="flex items-start gap-3 p-3 rounded-lg bg-surface-elevated/40 border border-white/5">
                <Eye className="w-4 h-4 text-ember-400 shrink-0 mt-0.5" />
                <div>
                  <span className="text-xs font-medium text-ember-400">Change of Character</span>
                  <p className="text-xs mt-1 text-[var(--color-text)]">{data.choch || 'Not detected'}</p>
                </div>
              </div>
            </div>
          </div>
        </Section>

        {/* Indicators */}
        <Section title="Indicators" icon={BarChart3} className="lg:col-span-2">
          <div className="grid grid-cols-3 gap-4">
            <div className="p-3 rounded-lg bg-surface-elevated/40 border border-white/5 text-center">
              <span className="text-xs text-[var(--color-text-muted)]">RSI</span>
              <p className="text-sm font-bold font-mono mt-1">{data.rsi || '-'}</p>
            </div>
            <div className="p-3 rounded-lg bg-surface-elevated/40 border border-white/5 text-center">
              <span className="text-xs text-[var(--color-text-muted)]">EMA</span>
              <p className="text-sm font-bold font-mono mt-1">{data.ema || '-'}</p>
            </div>
            <div className="p-3 rounded-lg bg-surface-elevated/40 border border-white/5 text-center">
              <span className="text-xs text-[var(--color-text-muted)]">Trend Strength</span>
              <p className="text-sm font-bold font-mono mt-1">{data.trendStrength || '-'}</p>
            </div>
          </div>
        </Section>
      </div>

      {data.entryIdeas.length > 0 && (
        <GlassCard className="p-5">
          <div className="flex items-center gap-2 mb-3">
            <Zap className="w-4 h-4 text-aurora-400" />
            <h3 className="text-sm font-semibold">Entry Ideas</h3>
          </div>
          <ul className="space-y-1">
            {data.entryIdeas.map((idea, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-[var(--color-text)]">
                <span className="text-aurora-400 mt-0.5">&#x2022;</span>
                {idea}
              </li>
            ))}
          </ul>
        </GlassCard>
      )}
    </motion.div>
  );
}
