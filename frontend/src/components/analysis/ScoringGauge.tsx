'use client';

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import { GlassCard } from '@/components/ui/GlassCard';
import { BarChart3, Eye, TrendingUp, Zap, Shield } from 'lucide-react';
import type { ScoringDetail } from '@/types/vision';

interface ScoringGaugeProps {
  scoring: ScoringDetail;
  className?: string;
}

const CATEGORIES = [
  { key: 'marketStructure' as const, label: 'Market Structure', weight: '30%', icon: BarChart3 },
  { key: 'liquidity' as const, label: 'Liquidity', weight: '25%', icon: Eye },
  { key: 'trend' as const, label: 'Trend', weight: '20%', icon: TrendingUp },
  { key: 'momentum' as const, label: 'Momentum', weight: '15%', icon: Zap },
  { key: 'confluence' as const, label: 'Confluence', weight: '10%', icon: Shield },
];

function scoreColor(score: number): string {
  if (score >= 80) return 'bg-aurora-400';
  if (score >= 60) return 'bg-aurora-500';
  if (score >= 40) return 'bg-ember-400';
  if (score >= 20) return 'bg-ember-500';
  return 'bg-red-400';
}

export function ScoringGauge({ scoring, className }: ScoringGaugeProps) {
  return (
    <GlassCard className={cn('p-5', className)}>
      <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/5">
        <BarChart3 className="w-4 h-4 text-cyber-400" />
        <h3 className="text-sm font-semibold">Scoring Breakdown</h3>
      </div>
      <div className="space-y-3">
        {CATEGORIES.map(({ key, label, weight, icon: Icon }) => {
          const score = scoring?.[key] ?? 0;
          return (
            <div key={key}>
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-1.5">
                  <Icon className="w-3 h-3 text-[var(--color-text-muted)]" />
                  <span className="text-xs text-[var(--color-text-muted)]">{label}</span>
                  <span className="text-[10px] text-[var(--color-text-muted)] opacity-50">({weight})</span>
                </div>
                <span className={cn('text-xs font-mono font-bold', score >= 60 ? 'text-aurora-400' : 'text-ember-400')}>{score}</span>
              </div>
              <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${score}%` }}
                  transition={{ duration: 0.8, ease: 'easeOut' }}
                  className={cn('h-full rounded-full', scoreColor(score))}
                />
              </div>
            </div>
          );
        })}
        <div className="pt-3 mt-3 border-t border-white/5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1">
              <span className="text-xs font-bold text-aurora-400">{scoring?.bullScore ?? 0}</span>
              <span className="text-[10px] text-[var(--color-text-muted)]">/</span>
              <span className="text-xs font-bold text-red-400">{scoring?.bearScore ?? 0}</span>
            </div>
            <span className="text-[10px] text-[var(--color-text-muted)]">Bull / Bear</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-[var(--color-text-muted)]">Overall</span>
            <span className={cn(
              'text-sm font-bold font-mono',
              (scoring?.overall ?? 0) >= 60 ? 'text-aurora-400' : 'text-ember-400'
            )}>{scoring?.overall ?? 0}</span>
          </div>
        </div>
      </div>
    </GlassCard>
  );
}
