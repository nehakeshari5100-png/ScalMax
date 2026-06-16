'use client';

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import { GlassCard } from '@/components/ui/GlassCard';
import {
  Shield, CheckCircle, XCircle, AlertTriangle,
  TrendingUp, Eye, Zap, Target, BarChart3, Activity, DollarSign,
} from 'lucide-react';
import type { ValidationReport as ValidationReportType } from '@/types/vision';

interface Props {
  report: ValidationReportType;
}

const LAYER_ICONS: Record<string, any> = {
  'Market Structure': TrendingUp,
  'Liquidity': Eye,
  'SMC Confirmation': Activity,
  'FVG / Order Block': Target,
  'Volume': BarChart3,
  'Momentum': Zap,
  'Risk Reward': DollarSign,
};

const STRENGTH_CONFIG: Record<string, { label: string; color: string; bg: string; border: string }> = {
  STRONG_SIGNAL: { label: 'STRONG SIGNAL', color: 'text-aurora-400', bg: 'bg-aurora-500/10', border: 'border-aurora-500/15' },
  VALID_SIGNAL: { label: 'VALID SIGNAL', color: 'text-cyber-400', bg: 'bg-cyber-500/10', border: 'border-cyber-500/15' },
  WATCHLIST: { label: 'WATCHLIST', color: 'text-ember-400', bg: 'bg-ember-500/10', border: 'border-ember-500/15' },
  NO_TRADE: { label: 'NO TRADE', color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/15' },
};

export function ValidationReportCard({ report }: Props) {
  const cfg = STRENGTH_CONFIG[report.signalStrength] || STRENGTH_CONFIG.NO_TRADE;
  const PassIcon = report.signalStrength === 'STRONG_SIGNAL' ? CheckCircle : report.signalStrength === 'VALID_SIGNAL' ? Shield : AlertTriangle;

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-2">
        <Shield className="w-5 h-5 text-cyber-400" />
        <h2 className="text-base font-bold">Signal Validation Engine</h2>
      </div>

      {/* Verdict Banner */}
      <GlassCard className={cn('p-4 border', cfg.border)}>
        <div className="flex items-center gap-4">
          <div className={cn('w-12 h-12 rounded-2xl flex items-center justify-center', cfg.bg)}>
            <PassIcon className={cn('w-6 h-6', cfg.color)} />
          </div>
          <div className="flex-1">
            <p className={cn('text-base font-bold', cfg.color)}>{cfg.label}</p>
            <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
              {report.passedLayers.length}/{report.layers.length} layers passed &middot; {report.finalScore}/100
            </p>
          </div>
          <div className={cn(
            'w-16 h-16 rounded-full flex items-center justify-center text-lg font-bold font-mono border-2',
            report.finalScore >= 80 ? 'border-aurora-500/30 text-aurora-400' :
            report.finalScore >= 70 ? 'border-cyber-500/30 text-cyber-400' :
            report.finalScore >= 60 ? 'border-ember-500/30 text-ember-400' :
            'border-red-500/30 text-red-400'
          )}>
            {report.finalScore}
          </div>
        </div>
      </GlassCard>

      {/* Layer Results */}
      <div className="space-y-2">
        {report.layers.map((layer, i) => {
          const Icon = LAYER_ICONS[layer.name] || Shield;
          return (
            <GlassCard key={i} className="p-3">
              <div className="flex items-start gap-3">
                <div className={cn(
                  'w-8 h-8 rounded-lg flex items-center justify-center shrink-0',
                  layer.passed ? 'bg-aurora-500/10' : 'bg-red-500/10'
                )}>
                  {layer.passed
                    ? <CheckCircle className="w-4 h-4 text-aurora-400" />
                    : <XCircle className="w-4 h-4 text-red-400" />
                  }
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <Icon className="w-3.5 h-3.5 text-[var(--color-text-muted)]" />
                    <span className="text-xs font-semibold">{layer.name}</span>
                    <span className={cn(
                      'text-[10px] font-mono ml-auto',
                      layer.passed ? 'text-aurora-400' : 'text-red-400'
                    )}>
                      {layer.score}/{layer.maxScore}
                    </span>
                  </div>
                  <p className="text-[11px] text-[var(--color-text-muted)] mt-0.5">{layer.details}</p>
                </div>
              </div>
            </GlassCard>
          );
        })}
      </div>
    </motion.div>
  );
}
