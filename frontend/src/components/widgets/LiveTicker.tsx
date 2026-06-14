'use client';

import { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { cn, formatPrice, formatPercent } from '@/lib/utils';
import { api } from '@/lib/api';
import { TrendingUp, TrendingDown, Loader2 } from 'lucide-react';
import type { Token } from '@/types';

export function LiveTicker() {
  const [tokens, setTokens] = useState<Token[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.getTokens().then(data => {
      setTokens(data);
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading || tokens.length === 0) {
    return (
      <div className="glass border-b border-white/5">
        <div className="flex items-center gap-2 px-4 py-1.5 text-xs text-[var(--color-text-muted)]">
          <Loader2 className="w-3 h-3 animate-spin" /> Loading ticker...
        </div>
      </div>
    );
  }

  return (
    <div className="glass border-b border-white/5 overflow-hidden">
      <div className="flex items-center gap-0 py-1.5 overflow-x-auto scrollbar-hide">
        <div className="flex gap-6 px-4">
          {tokens.map((token, i) => (
            <motion.div key={token.symbol} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }}
              className="flex items-center gap-3 shrink-0">
              <span className="text-xs font-semibold text-[var(--color-text)]">{token.symbol.replace('/USDT', '').replace('USDT', '')}</span>
              <span className="text-xs font-mono font-medium">{formatPrice(token.price)}</span>
              <span className={cn('flex items-center gap-0.5 text-xs font-medium', token.change24h >= 0 ? 'text-aurora-400' : 'text-red-400')}>
                {token.change24h >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                {formatPercent(token.change24h)}
              </span>
              {i < tokens.length - 1 && <div className="w-px h-4 bg-white/5" />}
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}
