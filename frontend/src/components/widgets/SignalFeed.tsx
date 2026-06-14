'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn, formatPrice } from '@/lib/utils';
import { GlassCard } from '@/components/ui/GlassCard';
import { Badge } from '@/components/ui/Badge';
import { api } from '@/lib/api';
import { TrendingUp, TrendingDown, Clock, Zap, ChevronRight, Loader2 } from 'lucide-react';
import type { SignalRecord } from '@/types/signals';

interface SignalFeedProps {
  className?: string;
  limit?: number;
  accountId?: string | null;
}

export function SignalFeed({ className, limit = 5 }: SignalFeedProps) {
  const [signals, setSignals] = useState<SignalRecord[]>([]);
  const [filter, setFilter] = useState<'all' | 'long' | 'short'>('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.listSignals({ page_size: limit }).then(res => {
      if (res.success) setSignals(res.data);
    }).catch(() => {}).finally(() => setLoading(false));
  }, [limit]);

  const filtered = signals.filter(s => filter === 'all' || s.direction === filter);

  const formatTs = (ts: number) => {
    const diff = Date.now() - ts * 1000;
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return new Date(ts * 1000).toLocaleDateString();
  };

  return (
    <GlassCard className={cn('p-0 overflow-hidden', className)}>
      <div className="flex items-center justify-between px-5 py-4 border-b border-white/5">
        <div className="flex items-center gap-2">
          <Zap className="w-4 h-4 text-ember-400" />
          <h3 className="text-sm font-semibold">Signal Feed</h3>
        </div>
        <div className="flex items-center gap-1">
          {(['all', 'long', 'short'] as const).map(f => (
            <button key={f} onClick={() => setFilter(f)}
              className={cn('px-2.5 py-1 text-xs rounded-md transition-colors',
                filter === f ? 'bg-aurora-500/15 text-aurora-400' : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'
              )}>
              {f === 'all' ? 'All' : f === 'long' ? 'Long' : 'Short'}
            </button>
          ))}
        </div>
      </div>

      <div className="divide-y divide-white/5">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-4 h-4 text-aurora-400 animate-spin" />
          </div>
        ) : (
          <AnimatePresence>
            {filtered.map((signal, i) => (
              <motion.div key={signal.id} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }}
                className="flex items-center justify-between px-5 py-3 hover:bg-white/[0.02] transition-colors cursor-pointer group">
                <div className="flex items-center gap-3">
                  <div className={cn('w-8 h-8 rounded-lg flex items-center justify-center',
                    signal.direction === 'long' ? 'bg-green-500/10' : 'bg-red-500/10')}>
                    {signal.direction === 'long' ? <TrendingUp className="w-4 h-4 text-green-400" /> : <TrendingDown className="w-4 h-4 text-red-400" />}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold">{signal.symbol.replace('USDT', '')}</span>
                      <Badge variant={signal.direction === 'long' ? 'long' : 'short'} size="sm">{signal.direction.toUpperCase()}</Badge>
                      <span className="text-xs font-mono text-[var(--color-text-muted)]">{signal.entry ? `$${formatPrice(signal.entry)}` : '-'}</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-[var(--color-text-muted)] mt-0.5">
                      <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{formatTs(signal.created_at)}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <div className={cn('text-sm font-bold font-mono', signal.confidence >= 80 ? 'text-aurora-400' : signal.confidence >= 60 ? 'text-ember-400' : 'text-red-400')}>
                      {signal.confidence}%
                    </div>
                    <div className="text-[10px] text-[var(--color-text-muted)]">Confidence</div>
                  </div>
                  <ChevronRight className="w-4 h-4 text-[var(--color-text-muted)] opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        )}
      </div>

      {!loading && filtered.length === 0 && (
        <div className="flex items-center justify-center py-8 text-sm text-[var(--color-text-muted)]">No signals</div>
      )}
    </GlassCard>
  );
}
