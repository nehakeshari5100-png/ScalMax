'use client';

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import { Bot, Brain, AlertTriangle, Target, Shield, ChevronDown, ChevronUp } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { GlassCard } from '@/components/ui/GlassCard';
import { useState } from 'react';

interface AIAnalysisPanelProps {
  analysis?: {
    direction: string;
    confidence: number;
    reasoning?: string;
    levels?: {
      entry: number | null;
      stop_loss: number | null;
      take_profit_1: number | null;
      take_profit_2: number | null;
      risk_reward_1?: number | null;
      risk_reward_2?: number | null;
    };
    model?: string;
    keyLevels?: { support: number[]; resistance: number[] };
    riskNotes?: string[];
  };
  symbol?: string;
  className?: string;
}

export function AIAnalysisPanel({ analysis, symbol = 'BTC/USDT', className }: AIAnalysisPanelProps) {
  const [expanded, setExpanded] = useState(false);

  if (!analysis) {
    return (
      <GlassCard className={cn('flex flex-col items-center justify-center py-8 text-center', className)}>
        <Bot className="w-10 h-10 text-[var(--color-text-muted)] mb-3" />
        <p className="text-sm text-[var(--color-text-muted)]">AI analysis not available</p>
        <p className="text-xs text-[var(--color-text-muted)] mt-1">Configure OpenRouter in Settings</p>
      </GlassCard>
    );
  }

  const confidence = analysis.confidence || 0;
  const direction = analysis.direction || 'neutral';
  const model = analysis.model || 'decision-engine';
  const reasoning = analysis.reasoning || '';
  const levels = analysis.levels || { entry: null, stop_loss: null, take_profit_1: null, take_profit_2: null };
  const keyLevels = analysis.keyLevels || { support: [], resistance: [] };
  const riskNotes = analysis.riskNotes || [];

  return (
    <GlassCard className={cn('space-y-4', className)} glow="green">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-aurora-500 to-cyber-600 flex items-center justify-center">
            <Brain className="w-3.5 h-3.5 text-white" />
          </div>
          <div>
            <h3 className="text-sm font-semibold">AI Analyst</h3>
            <p className="text-[10px] text-[var(--color-text-muted)] font-mono">{model}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant={direction === 'long' ? 'long' : 'short'}>
            {direction.toUpperCase()} {confidence}%
          </Badge>
        </div>
      </div>

      <div className="relative">
        <div className="h-1.5 bg-surface-dark/60 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${confidence}%` }}
            transition={{ duration: 1, ease: 'easeOut' }}
            className={cn(
              'h-full rounded-full',
              confidence >= 80 ? 'bg-aurora-400' : confidence >= 60 ? 'bg-ember-400' : 'bg-red-400'
            )}
          />
        </div>
        <span className="text-[10px] text-[var(--color-text-muted)] mt-1 block">Confidence score</span>
      </div>

      {reasoning && (
        <p className="text-xs leading-relaxed text-[var(--color-text-secondary)]">{reasoning}</p>
      )}

      {keyLevels.support.length > 0 && keyLevels.resistance.length > 0 && (
        <div className="grid grid-cols-2 gap-3">
          <div className="glass-card p-3 border-green-500/10">
            <div className="flex items-center gap-1.5 mb-2">
              <Target className="w-3 h-3 text-aurora-400" />
              <span className="text-xs font-medium text-aurora-400">Support</span>
            </div>
            <div className="space-y-1">
              {keyLevels.support.map((level, i) => (
                <div key={i} className="flex items-center justify-between text-xs font-mono">
                  <span className="text-[var(--color-text-muted)]">S{i + 1}</span>
                  <span className="text-[var(--color-text)]">${level.toFixed(2)}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="glass-card p-3 border-red-500/10">
            <div className="flex items-center gap-1.5 mb-2">
              <Target className="w-3 h-3 text-red-400" />
              <span className="text-xs font-medium text-red-400">Resistance</span>
            </div>
            <div className="space-y-1">
              {keyLevels.resistance.map((level, i) => (
                <div key={i} className="flex items-center justify-between text-xs font-mono">
                  <span className="text-[var(--color-text-muted)]">R{i + 1}</span>
                  <span className="text-[var(--color-text)]">${level.toFixed(2)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {levels.entry && (
        <div className="grid grid-cols-3 gap-2">
          <div className="glass-card p-2 text-center">
            <span className="text-[10px] text-[var(--color-text-muted)]">Entry</span>
            <p className="text-xs font-mono font-bold">${levels.entry.toFixed(2)}</p>
          </div>
          <div className="glass-card p-2 text-center border-red-500/10">
            <span className="text-[10px] text-[var(--color-text-muted)]">SL</span>
            <p className="text-xs font-mono font-bold text-red-400">{levels.stop_loss ? `$${levels.stop_loss.toFixed(2)}` : '-'}</p>
          </div>
          <div className="glass-card p-2 text-center border-aurora-500/10">
            <span className="text-[10px] text-[var(--color-text-muted)]">TP</span>
            <p className="text-xs font-mono font-bold text-aurora-400">{levels.take_profit_1 ? `$${levels.take_profit_1.toFixed(2)}` : '-'}</p>
          </div>
        </div>
      )}

      {riskNotes.length > 0 && (
        <div>
          <button onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1 text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors">
            <Shield className="w-3 h-3" /> Risk Notes ({riskNotes.length})
            {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          </button>
          {expanded && (
            <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} className="mt-2 space-y-1.5">
              {riskNotes.map((note, i) => (
                <div key={i} className="flex items-start gap-2 text-xs text-[var(--color-text-muted)]">
                  <AlertTriangle className="w-3 h-3 text-ember-400 shrink-0 mt-0.5" />
                  <span>{note}</span>
                </div>
              ))}
            </motion.div>
          )}
        </div>
      )}
    </GlassCard>
  );
}
