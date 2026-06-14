'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import { PageContainer } from '@/components/layout/PageContainer';
import { GlassCard } from '@/components/ui/GlassCard';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { api } from '@/lib/api';
import { formatPrice, formatPercent } from '@/lib/utils';
import { Search, Loader2, XCircle, TrendingUp, TrendingDown, Minus, RefreshCw, Zap } from 'lucide-react';

const SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT'];

interface ScannerItem {
  symbol: string;
  price: number;
  change24h: number;
  volume: number;
  direction: string;
  confidence: number;
  score: number;
  loading: boolean;
}

export default function ScannerPage() {
  const [results, setResults] = useState<ScannerItem[]>([]);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<'all' | 'long' | 'short' | 'neutral'>('all');
  const [sortBy, setSortBy] = useState<'confidence' | 'score' | 'volume' | 'change'>('confidence');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const items: ScannerItem[] = SYMBOLS.map(s => ({ symbol: s, price: 0, change24h: 0, volume: 0, direction: 'neutral', confidence: 0, score: 0, loading: true }));
      setResults(items);

      const results = await Promise.allSettled(
        SYMBOLS.map(async (sym) => {
          const pipeRes = await api.quickAnalysis({ symbol: sym, timeframe: '5m', lookback: 200 });
          if (pipeRes.success) {
            return {
              symbol: sym,
              price: 0,
              change24h: 0,
              volume: 0,
              direction: pipeRes.decision?.direction || 'neutral',
              confidence: pipeRes.decision?.confidence || 0,
              score: pipeRes.decision?.confidence || 0,
              loading: false,
            };
          }
          return { symbol: sym, price: 0, change24h: 0, volume: 0, direction: 'neutral', confidence: 0, score: 0, loading: false };
        })
      );

      const completed = results.map((r, i) => {
        if (r.status === 'fulfilled') return r.value;
        return { symbol: SYMBOLS[i], price: 0, change24h: 0, volume: 0, direction: 'neutral', confidence: 0, score: 0, loading: false };
      });

      try {
        const tokens = await api.getTokens();
        const tokenMap = new Map(tokens.map(t => [t.symbol, t]));
        completed.forEach(item => {
          const tok = tokenMap.get(item.symbol);
          if (tok) {
            item.price = tok.price;
            item.change24h = tok.change24h;
            item.volume = tok.volume24h;
          }
        });
      } catch {}

      setResults(completed);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to scan');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const filtered = results
    .filter(r => !search || r.symbol.toLowerCase().includes(search.toLowerCase()))
    .filter(r => filter === 'all' || r.direction === filter);

  const sorted = [...filtered].sort((a, b) => {
    if (sortBy === 'confidence') return b.confidence - a.confidence;
    if (sortBy === 'score') return b.score - a.score;
    if (sortBy === 'volume') return b.volume - a.volume;
    return Math.abs(b.change24h) - Math.abs(a.change24h);
  });

  if (loading && results.length === 0) return (
    <PageContainer>
      <div className="flex items-center justify-center h-96">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-8 h-8 text-aurora-400 animate-spin" />
          <p className="text-sm text-[var(--color-text-muted)]">Analyzing markets...</p>
        </div>
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
        <div className="flex items-center gap-3">
          <Zap className="w-5 h-5 text-aurora-400" />
          <h1 className="text-lg font-bold">Market Scanner</h1>
          <Badge variant="info">{results.length} pairs</Badge>
        </div>
        <Button variant="outline" onClick={load}>
          <RefreshCw className="w-4 h-4 mr-1" /> Refresh
        </Button>
      </div>

      <GlassCard className="mb-6">
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex-1 min-w-[200px]">
            <Input
              placeholder="Search symbol..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              icon={<Search className="w-4 h-4" />}
            />
          </div>
          <div className="flex gap-1">
            {(['all', 'long', 'short', 'neutral'] as const).map(f => (
              <button key={f} onClick={() => setFilter(f)}
                className={cn('px-3 py-1.5 text-xs rounded-lg transition', filter === f ? 'bg-aurora-500/15 text-aurora-400' : 'text-[var(--color-text-muted)] hover:text-white')}>
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>
          <select value={sortBy} onChange={e => setSortBy(e.target.value as 'confidence' | 'score' | 'volume' | 'change')}
            className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-[var(--color-text-muted)]">
            <option value="confidence">Confidence</option>
            <option value="score">Score</option>
            <option value="volume">Volume</option>
            <option value="change">Change</option>
          </select>
        </div>
      </GlassCard>

      <div className="grid gap-4">
        {sorted.map(item => (
          <GlassCard key={item.symbol}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-sm font-semibold w-16">{item.symbol.replace('USDT', '')}</span>
                <span className="text-xs font-mono">{item.price > 0 ? formatPrice(item.price) : '-'}</span>
                {item.change24h !== 0 && (
                  <span className={cn('text-xs flex items-center gap-1', item.change24h >= 0 ? 'text-aurora-400' : 'text-red-400')}>
                    {item.change24h >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                    {formatPercent(item.change24h)}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-4">
                <div className="text-right">
                  <p className="text-[10px] text-[var(--color-text-muted)]">Confidence</p>
                  <p className={cn('text-xs font-bold', item.confidence >= 70 ? 'text-aurora-400' : item.confidence >= 50 ? 'text-yellow-400' : 'text-[var(--color-text-muted)]')}>
                    {item.confidence}%
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-[10px] text-[var(--color-text-muted)]">Score</p>
                  <p className="text-xs font-mono">{item.score}</p>
                </div>
                <Badge variant={item.direction === 'long' ? 'long' : item.direction === 'short' ? 'short' : 'info'} size="sm">
                  {item.direction.toUpperCase()}
                </Badge>
              </div>
            </div>
          </GlassCard>
        ))}
        {sorted.length === 0 && (
          <p className="text-xs text-[var(--color-text-muted)] text-center py-8">No results match your filters</p>
        )}
      </div>
    </PageContainer>
  );
}
