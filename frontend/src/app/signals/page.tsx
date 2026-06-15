'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn, formatPrice, formatTimestamp } from '@/lib/utils';
import { PageContainer } from '@/components/layout/PageContainer';
import { GlassCard } from '@/components/ui/GlassCard';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { api } from '@/lib/api';
import {
  TrendingUp, TrendingDown, Clock, Zap, Filter, ArrowUp, ArrowDown,
  Target, Shield, Brain, ChevronDown, ChevronUp, Download, Search, Loader2, XCircle
} from 'lucide-react';
import type { SignalRecord } from '@/types/signals';

export default function SignalsPage() {
  const [signals, setSignals] = useState<SignalRecord[]>([]);
  const [selectedSignal, setSelectedSignal] = useState<SignalRecord | null>(null);
  const [statusFilter, setStatusFilter] = useState('all');
  const [directionFilter, setDirectionFilter] = useState('all');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string | number> = { page_size: 50 };
      if (statusFilter !== 'all') params.status = statusFilter;
      if (directionFilter !== 'all') params.direction = directionFilter;
      if (search) params.search = search;
      const res = await api.listSignals(params);
      if (res.success) setSignals(res.data);
      else setError(res.error || 'Failed to load signals');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load signals');
    } finally {
      setLoading(false);
    }
  }, [statusFilter, directionFilter, search]);

  useEffect(() => { load(); }, [load]);

  const filtered = signals;

  const statusVariant = (s: string) => {
    switch (s) {
      case 'active': return 'success' as const;
      case 'triggered': return 'info' as const;
      case 'completed': return 'success' as const;
      case 'cancelled': return 'neutral' as const;
      case 'expired': return 'neutral' as const;
      default: return 'neutral' as const;
    }
  };

  const directionVariant = (d: string) => d === 'long' ? 'long' as const : 'short' as const;

  const signalTypeLabel = (t: string) => {
    switch (t) {
      case 'strong_buy': return 'Strong Buy';
      case 'buy': return 'Buy';
      case 'sell': return 'Sell';
      case 'strong_sell': return 'Strong Sell';
      default: return 'Neutral';
    }
  };

  const formatTimestamp2 = (ts: number) => {
    const d = new Date(ts * 1000);
    const now = Date.now();
    const diff = now - d.getTime();
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return d.toLocaleDateString();
  };

  if (loading && signals.length === 0) return (
    <PageContainer>
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 text-aurora-400 animate-spin" />
      </div>
    </PageContainer>
  );

  if (error) return (
    <PageContainer>
      <GlassCard className="flex flex-col items-center gap-4 p-12">
        <XCircle className="w-10 h-10 text-red-400" />
        <p className="text-sm text-red-400">{error}</p>
        <Button variant="outline" onClick={load}>Retry</Button>
      </GlassCard>
    </PageContainer>
  );

  return (
    <PageContainer>
      <div className="flex items-center justify-between mb-6">
        <div>
          <p className="text-sm text-[var(--color-text-secondary)]">{filtered.length} signals found</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <input
              type="text"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search symbol..."
              className="glass-input w-40 pl-8 py-1.5 text-xs"
            />
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3 h-3 text-[var(--color-text-muted)]" />
          </div>
          <div className="flex items-center gap-1 bg-surface-dark/60 rounded-lg p-1 border border-white/5">
            {['all', 'active', 'completed', 'cancelled', 'expired'].map(status => (
              <button key={status} onClick={() => setStatusFilter(status)}
                className={cn('px-2.5 py-1 text-xs rounded-md transition-colors capitalize',
                  statusFilter === status ? 'bg-aurora-500/15 text-aurora-400' : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'
                )}>
                {status}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2 space-y-3">
          <AnimatePresence>
            {filtered.map((signal, i) => (
              <motion.div key={signal.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.02 }}>
                <GlassCard
                  className={cn('p-0 overflow-hidden cursor-pointer transition-all duration-200',
                    selectedSignal?.id === signal.id && 'border-aurora-500/30 shadow-glow'
                  )}
                  hover={false}
                  onClick={() => setSelectedSignal(signal)}
                >
                  <div className="p-5">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <div className={cn('w-10 h-10 rounded-xl flex items-center justify-center',
                          signal.direction === 'long' ? 'bg-green-500/10' : 'bg-red-500/10'
                        )}>
                          {signal.direction === 'long' ? <ArrowUp className="w-5 h-5 text-green-400" /> : <ArrowDown className="w-5 h-5 text-red-400" />}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-base font-bold">{signal.symbol.replace('USDT', '')}</span>
                            <Badge variant={directionVariant(signal.direction)}>{signal.direction.toUpperCase()}</Badge>
                            <Badge variant={statusVariant(signal.status)}>{signal.status}</Badge>
                            <span className="text-xs text-[var(--color-text-muted)] font-mono">{signal.signal_type.replace('_', ' ').toUpperCase()}</span>
                          </div>
                          <div className="flex items-center gap-2 text-xs text-[var(--color-text-muted)] mt-0.5">
                            <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {formatTimestamp2(signal.created_at)}</span>
                            <span>·</span>
                            <span>{signal.timeframe}</span>
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className={cn('text-lg font-bold font-mono',
                          signal.confidence >= 80 ? 'text-aurora-400' : signal.confidence >= 60 ? 'text-ember-400' : 'text-red-400'
                        )}>
                          {signal.confidence}%
                        </div>
                        <div className="text-[10px] text-[var(--color-text-muted)] uppercase">Confidence</div>
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <div className="text-[10px] text-[var(--color-text-muted)] uppercase">Entry</div>
                        <div className="text-sm font-mono font-medium">{signal.entry ? `$${formatPrice(signal.entry)}` : '-'}</div>
                      </div>
                      <div>
                        <div className="text-[10px] text-[var(--color-text-muted)] uppercase">Stop Loss</div>
                        <div className="text-sm font-mono font-medium text-red-400">{signal.stop_loss ? `$${formatPrice(signal.stop_loss)}` : '-'}</div>
                      </div>
                      <div>
                        <div className="text-[10px] text-[var(--color-text-muted)] uppercase">Take Profit</div>
                        <div className="flex gap-1 text-sm font-mono font-medium text-aurora-400">
                          {signal.take_profit_1 ? `$${formatPrice(signal.take_profit_1)}` : '-'}
                          {signal.take_profit_2 ? `, $${formatPrice(signal.take_profit_2)}` : ''}
                        </div>
                      </div>
                    </div>

                    <div className="mt-3 pt-3 border-t border-white/5">
                      <div className="flex items-center gap-4">
                        <div className="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)]">
                          <Zap className="w-3 h-3 text-aurora-400" />
                          Confluence: {signal.confluence_score}
                        </div>
                        <div className="flex items-center gap-1.5 text-xs text-[var(--color-text-muted)]">
                          <Shield className="w-3 h-3 text-cyber-400" />
                          RR: {signal.risk_reward_1?.toFixed(2) || '-'}
                        </div>
                      </div>
                    </div>
                  </div>
                </GlassCard>
              </motion.div>
            ))}
          </AnimatePresence>
          {filtered.length === 0 && (
            <p className="text-xs text-[var(--color-text-muted)] text-center py-12">No signals match your filters</p>
          )}
        </div>

        <div className="space-y-4">
          {selectedSignal ? (
            <>
              <GlassCard className="p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold">Signal Details</h3>
                </div>
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="glass-card p-3">
                      <div className="text-[10px] text-[var(--color-text-muted)] uppercase">Entry Price</div>
                      <div className="text-sm font-mono font-bold">{selectedSignal.entry ? `$${formatPrice(selectedSignal.entry)}` : '-'}</div>
                    </div>
                    <div className="glass-card p-3 border-red-500/10">
                      <div className="text-[10px] text-[var(--color-text-muted)] uppercase">Stop Loss</div>
                      <div className="text-sm font-mono font-bold text-red-400">{selectedSignal.stop_loss ? `$${formatPrice(selectedSignal.stop_loss)}` : '-'}</div>
                    </div>
                    <div className="glass-card p-3 border-aurora-500/10">
                      <div className="text-[10px] text-[var(--color-text-muted)] uppercase">TP 1</div>
                      <div className="text-sm font-mono font-bold text-aurora-400">{selectedSignal.take_profit_1 ? `$${formatPrice(selectedSignal.take_profit_1)}` : '-'}</div>
                    </div>
                    {selectedSignal.take_profit_2 && (
                      <div className="glass-card p-3 border-aurora-500/10">
                        <div className="text-[10px] text-[var(--color-text-muted)] uppercase">TP 2</div>
                        <div className="text-sm font-mono font-bold text-aurora-400">${formatPrice(selectedSignal.take_profit_2)}</div>
                      </div>
                    )}
                  </div>
                  <div className="glass-card p-3">
                    <div className="text-[10px] text-[var(--color-text-muted)] uppercase">Reasoning</div>
                    <p className="text-xs text-[var(--color-text-secondary)] mt-1">{selectedSignal.reasoning || 'No reasoning provided'}</p>
                  </div>
                  {selectedSignal.reasons.length > 0 && (
                    <div className="glass-card p-3">
                      <div className="text-[10px] text-[var(--color-text-muted)] uppercase">Reasons</div>
                      <ul className="text-xs text-[var(--color-text-secondary)] mt-1 space-y-0.5">
                        {selectedSignal.reasons.map((r, i) => <li key={i}>• {r}</li>)}
                      </ul>
                    </div>
                  )}
                  {selectedSignal.risks.length > 0 && (
                    <div className="glass-card p-3 border-amber-500/10">
                      <div className="text-[10px] text-[var(--color-text-muted)] uppercase">Risks</div>
                      <ul className="text-xs text-amber-400/80 mt-1 space-y-0.5">
                        {selectedSignal.risks.map((r, i) => <li key={i}>• {r}</li>)}
                      </ul>
                    </div>
                  )}
                  {selectedSignal.pnl !== null && (
                    <div className="glass-card p-3">
                      <div className="text-[10px] text-[var(--color-text-muted)] uppercase">P&L</div>
                      <span className={cn('text-sm font-bold font-mono', (selectedSignal.pnl || 0) >= 0 ? 'text-aurora-400' : 'text-red-400')}>
                        {(selectedSignal.pnl ?? 0) >= 0 ? '+' : ''}${(selectedSignal.pnl ?? 0).toFixed(2)} ({selectedSignal.pnl_pct?.toFixed(2) || '0'}%)
                      </span>
                    </div>
                  )}
                </div>
              </GlassCard>
            </>
          ) : (
            <GlassCard className="flex flex-col items-center justify-center py-12 text-center">
              <Target className="w-12 h-12 text-[var(--color-text-muted)] mb-3" />
              <p className="text-sm text-[var(--color-text-muted)]">Select a signal to view details</p>
              <p className="text-xs text-[var(--color-text-muted)] mt-1">Click on any signal from the list</p>
            </GlassCard>
          )}
        </div>
      </div>
    </PageContainer>
  );
}
