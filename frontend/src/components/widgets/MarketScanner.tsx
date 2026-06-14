'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { cn, formatPrice, formatPercent } from '@/lib/utils';
import { GlassCard } from '@/components/ui/GlassCard';
import { Badge } from '@/components/ui/Badge';
import { api } from '@/lib/api';
import { Search, TrendingUp, TrendingDown, Minus, Loader2 } from 'lucide-react';
import type { Token } from '@/types';

interface MarketScannerProps {
  className?: string;
}

export function MarketScanner({ className }: MarketScannerProps) {
  const [results, setResults] = useState<Token[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    setLoading(true);
    api.getTokens().then(data => {
      setResults(data);
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const filtered = results.filter(r => r.symbol.toLowerCase().includes(search.toLowerCase()));

  const signal = (change: number) => {
    if (change > 0.5) return 'long';
    if (change < -0.5) return 'short';
    return 'neutral';
  };

  return (
    <GlassCard className={cn('p-0 overflow-hidden', className)}>
      <div className="flex items-center justify-between px-5 py-4 border-b border-white/5">
        <div className="flex items-center gap-2">
          <Search className="w-4 h-4 text-cyber-400" />
          <h3 className="text-sm font-semibold">Market Scanner</h3>
        </div>
        <div className="relative">
          <input type="text" value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Filter..." className="bg-surface-dark/60 border border-white/5 rounded-lg pl-8 pr-3 py-1.5 text-xs text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:border-aurora-500/30 w-32" />
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[var(--color-text-muted)]" />
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-4 h-4 text-aurora-400 animate-spin" />
        </div>
      ) : (
        <div className="divide-y divide-white/5">
          {filtered.map((result, i) => {
            const sig = signal(result.change24h);
            const SignalIcon = sig === 'long' ? TrendingUp : sig === 'short' ? TrendingDown : Minus;
            return (
              <motion.div key={result.symbol} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.03 }}
                className="flex items-center justify-between px-5 py-3 hover:bg-white/[0.02] transition-colors">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-8 h-8 rounded-lg bg-surface-elevated/60 flex items-center justify-center text-xs font-bold font-mono">
                    {result.symbol.replace('/USDT', '').replace('USDT', '')}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold">{result.symbol.replace('/USDT', '').replace('USDT', '')}</span>
                      <span className="text-xs font-mono text-[var(--color-text)]">{formatPrice(result.price)}</span>
                      <span className={cn('text-xs font-medium', result.change24h >= 0 ? 'text-aurora-400' : 'text-red-400')}>
                        {formatPercent(result.change24h)}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right hidden sm:block">
                    <div className="text-xs text-[var(--color-text-muted)]">Vol ${(result.volume24h / 1e6).toFixed(1)}M</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className={cn('w-7 h-7 rounded-lg flex items-center justify-center',
                      sig === 'long' ? 'bg-green-500/10' : sig === 'short' ? 'bg-red-500/10' : 'bg-yellow-500/10')}>
                      <SignalIcon className={cn('w-3.5 h-3.5', sig === 'long' ? 'text-green-400' : sig === 'short' ? 'text-red-400' : 'text-yellow-400')} />
                    </div>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}

      {!loading && filtered.length === 0 && (
        <div className="flex items-center justify-center py-8 text-sm text-[var(--color-text-muted)]">No results</div>
      )}
    </GlassCard>
  );
}
