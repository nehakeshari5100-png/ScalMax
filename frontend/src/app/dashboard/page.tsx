'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import { PageContainer } from '@/components/layout/PageContainer';
import { GlassCard } from '@/components/ui/GlassCard';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { PortfolioStats, PortfolioEquity } from '@/components/widgets/PortfolioStats';
import { SignalFeed } from '@/components/widgets/SignalFeed';
import { MarketScanner } from '@/components/widgets/MarketScanner';
import { TradingViewChart } from '@/components/widgets/TradingViewChart';
import { AIAnalysisPanel } from '@/components/widgets/AIAnalysisPanel';
import { TrendingUp, TrendingDown, ArrowUp, ArrowDown, Activity, DollarSign, BarChart3, Clock, Zap, Loader2, XCircle, Eye, EyeOff } from 'lucide-react';
import { formatPrice, formatPercent } from '@/lib/utils';
import { api } from '@/lib/api';
import { AreaChart, Area, ResponsiveContainer, XAxis, YAxis, Tooltip } from 'recharts';
import type { SignalRecord } from '@/types/signals';
import type { Position } from '@/types/papertrading';

export default function DashboardPage() {
  const [showBalances, setShowBalances] = useState(true);
  const [selectedTimeframe, setSelectedTimeframe] = useState('24H');

  const [accountId, setAccountId] = useState<string | null>(null);
  const [signals, setSignals] = useState<SignalRecord[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [tickers, setTickers] = useState<{ symbol: string; price: number; change24h: number }[]>([]);
  const [equityData, setEquityData] = useState<{ date: string; value: number }[]>([]);
  const [analysis, setAnalysis] = useState<import('@/types/decision').DecisionOutput | null>(null);
  const [pageLoading, setPageLoading] = useState(true);
  const [pageError, setPageError] = useState<string | null>(null);

  const loadAccount = useCallback(async () => {
    let id = localStorage.getItem('scalpex_paper_account');
    if (id) {
      const acct = await api.getPaperAccount(id);
      if (acct.success && acct.data) return acct.data.id;
    }
    const acct = await api.createPaperAccount({ name: 'Default', initial_balance: 10000 });
    if (acct.success && acct.data) {
      localStorage.setItem('scalpex_paper_account', acct.data.id);
      return acct.data.id;
    }
    return null;
  }, []);

  const loadAll = useCallback(async () => {
    setPageLoading(true);
    setPageError(null);
    try {
      const aid = await loadAccount();
      setAccountId(aid);

      const [sigRes, posRes, statRes] = await Promise.all([
        api.listSignals({ page_size: 5 }),
        aid ? api.listPaperPositions({ account_id: aid, status: 'open' }) : Promise.resolve(null),
        aid ? api.getPaperStats(aid) : Promise.resolve(null),
      ]);

      if (sigRes.success) setSignals(sigRes.data);
      if (posRes?.success) setPositions(posRes.data);

      if (statRes?.success && statRes.data) {
        const days = statRes.data.daily_pnl || {};
        const sorted = Object.entries(days).sort(([a], [b]) => a.localeCompare(b));
        let cum = 10000;
        setEquityData(sorted.map(([date, pnl]) => {
          cum += pnl;
          return { date: date.slice(5), value: Math.round(cum * 100) / 100 };
        }));
      }

      try {
        const pipeRes = await api.quickAnalysis({ symbol: 'BTCUSDT', timeframe: '5m', lookback: 200 });
        if (pipeRes.success && pipeRes.decision) setAnalysis(pipeRes.decision);
      } catch {}
    } catch (e) {
      setPageError(e instanceof Error ? e.message : 'Failed to load dashboard data');
    } finally {
      setPageLoading(false);
    }
  }, [loadAccount]);

  useEffect(() => { loadAll(); }, [loadAll]);

  if (pageLoading) {
    return (
      <PageContainer>
        <div className="flex items-center justify-center h-96">
          <div className="flex flex-col items-center gap-4">
            <Loader2 className="w-8 h-8 text-aurora-400 animate-spin" />
            <p className="text-sm text-[var(--color-text-muted)]">Loading dashboard...</p>
          </div>
        </div>
      </PageContainer>
    );
  }

  if (pageError) {
    return (
      <PageContainer>
        <GlassCard className="flex flex-col items-center justify-center gap-4 p-12">
          <XCircle className="w-10 h-10 text-red-400" />
          <p className="text-sm text-red-400">{pageError}</p>
          <Button variant="outline" onClick={loadAll}>Retry</Button>
        </GlassCard>
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      <PortfolioStats accountId={accountId} className="mb-6" />

      <div className="grid lg:grid-cols-3 gap-6 mb-6">
        <div className="lg:col-span-2">
          <TradingViewChart symbol="BTCUSDT" height={420} />
        </div>

        <div className="space-y-6">
          {analysis && (
            <AIAnalysisPanel
              analysis={{
                direction: analysis.direction,
                confidence: analysis.confidence,
                reasoning: analysis.reasoning,
                levels: analysis.levels,
              }}
              symbol="BTCUSDT"
            />
          )}

          <GlassCard>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold flex items-center gap-2">
                <Activity className="w-4 h-4 text-aurora-400" />
                Market Overview
              </h3>
            </div>
            <div className="space-y-2">
              {signals.slice(0, 4).map(s => (
                <div key={s.id} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold w-10">{s.symbol.replace('USDT', '')}</span>
                    <span className="text-xs font-mono">{s.entry ? formatPrice(s.entry) : '-'}</span>
                  </div>
                  <Badge variant={s.signal_type === 'strong_buy' || s.signal_type === 'buy' ? 'long' : 'short'} size="sm">
                    {s.signal_type.replace('_', ' ').toUpperCase()}
                  </Badge>
                </div>
              ))}
              {signals.length === 0 && (
                <p className="text-xs text-[var(--color-text-muted)] text-center py-4">No recent signals</p>
              )}
            </div>
          </GlassCard>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <GlassCard className="p-0 overflow-hidden">
          <div className="flex items-center justify-between px-5 py-4 border-b border-white/5">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-cyber-400" />
              <h3 className="text-sm font-semibold">Open Positions</h3>
            </div>
            <Badge variant="info">{positions.length} open</Badge>
          </div>
          <div className="divide-y divide-white/5">
            {positions.map(pos => (
              <div key={pos.id} className="px-5 py-3">
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold">{pos.symbol.replace('USDT', '')}</span>
                    <Badge variant={pos.direction === 'long' ? 'long' : 'short'} size="sm">{pos.direction.toUpperCase()}</Badge>
                  </div>
                  <span className={cn('text-sm font-bold font-mono', (pos.pnl || 0) >= 0 ? 'text-aurora-400' : 'text-red-400')}>
                    {(pos.pnl ?? 0) >= 0 ? '+' : ''}${(pos.pnl?.toFixed?.(2) ?? "0.00")}
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs text-[var(--color-text-muted)]">
                   <span>Entry: ${(pos.entry_price?.toFixed?.(2) ?? "0.00")}</span>
                   <span>Size: {(pos.quantity?.toFixed?.(4) ?? "0.0000")}</span>
                   <span>{(pos.pnl_pct ?? 0) >= 0 ? '+' : ''}{(pos.pnl_pct?.toFixed?.(2) ?? "0.00")}%</span>
                </div>
              </div>
            ))}
            {positions.length === 0 && (
              <p className="text-xs text-[var(--color-text-muted)] text-center py-8">No open positions</p>
            )}
          </div>
        </GlassCard>

        <SignalFeed limit={4} accountId={accountId} />
        <MarketScanner />
      </div>

      {equityData.length > 0 && (
        <GlassCard className="mt-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <DollarSign className="w-4 h-4 text-aurora-400" />
              <h3 className="text-sm font-semibold">Equity Curve</h3>
            </div>
          </div>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={equityData}>
                <defs>
                  <linearGradient id="eqGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#00c48c" stopOpacity={0.2} />
                    <stop offset="100%" stopColor="#00c48c" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 10 }} />
                <YAxis domain={['auto', 'auto']} axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 10 }} />
                <Tooltip contentStyle={{ background: '#111827', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '8px', fontSize: '12px' }} />
                <Area type="monotone" dataKey="value" stroke="#00c48c" strokeWidth={2} fill="url(#eqGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>
      )}
    </PageContainer>
  );
}
