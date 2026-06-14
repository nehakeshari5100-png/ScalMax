'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { PageContainer } from '@/components/layout/PageContainer';
import { GlassCard } from '@/components/ui/GlassCard';
import { api } from '@/lib/api';
import { Loader2, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis, Tooltip, AreaChart, Area, PieChart, Pie, Cell } from 'recharts';

const COLORS = ['#00c48c', '#ef4444', '#f59e0b', '#6366f1', '#ec4899'];

function MetricCard({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <GlassCard>
      <p className="text-xs text-[var(--color-text-muted)] mb-1">{label}</p>
      <p className="text-lg font-bold font-mono">{value}</p>
      {sub && <p className="text-[10px] text-[var(--color-text-muted)] mt-0.5">{sub}</p>}
    </GlassCard>
  );
}

export default function AnalyticsPage() {
  const [accountId, setAccountId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<import('@/types/papertrading').PerformanceStats | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      let aid = localStorage.getItem('scalpex_paper_account');
      if (!aid) {
        const acct = await api.createPaperAccount({ name: 'Default', initial_balance: 10000 });
        if (acct.success && acct.data) {
          aid = acct.data.id;
          localStorage.setItem('scalpex_paper_account', aid);
        }
      }
      setAccountId(aid);
      if (!aid) { setError('No account'); setLoading(false); return; }
      const res = await api.getPaperStats(aid);
      if (res.success && res.data) setStats(res.data);
      else setError(res.error || 'Failed to load stats');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) return (
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

  const equityCurve = stats?.daily_pnl ? (() => {
    const days = Object.entries(stats.daily_pnl).sort(([a], [b]) => a.localeCompare(b));
    let cum = 10000;
    return days.map(([date, pnl]) => {
      cum += (pnl as number);
      return { date: date.slice(5), value: Math.round(cum * 100) / 100 };
    });
  })() : [];

  const monthlyReturns = stats?.monthly_pnl ? Object.entries(stats.monthly_pnl).sort(([a], [b]) => a.localeCompare(b)).map(([m, p]) => ({ month: m, pnl: p as number })) : [];
  const winPct = stats?.win_rate || 0;
  const lossPct = 100 - winPct;
  const pieData = [
    { name: 'Wins', value: Math.max(winPct, 1) },
    { name: 'Losses', value: Math.max(lossPct, 1) },
  ];

  return (
    <PageContainer>
      <div className="grid grid-cols-4 gap-4 mb-6">
        <MetricCard label="Win Rate" value={`${(stats?.win_rate || 0).toFixed(1)}%`} />
        <MetricCard label="Profit Factor" value={(stats?.profit_factor || 0).toFixed(2)} />
        <MetricCard label="Total P&L" value={`$${(stats?.total_pnl || 0).toFixed(2)}`} sub={`${stats?.total_trades || 0} trades`} />
        <MetricCard label="Sharpe" value={(stats?.sharpe_ratio || 0).toFixed(2)} />
        <MetricCard label="Max Drawdown" value={`${(stats?.max_drawdown || 0).toFixed(1)}%`} />
        <MetricCard label="Avg RR" value={(stats?.avg_rr || 0).toFixed(2)} />
        <MetricCard label="Avg Trade" value={`$${(stats?.avg_pnl || 0).toFixed(2)}`} />
        <MetricCard label="Best / Worst" value={`$${(stats?.best_trade || 0).toFixed(0)} / $${(stats?.worst_trade || 0).toFixed(0)}`} />
      </div>

      <div className="grid grid-cols-2 gap-6 mb-6">
        <GlassCard className="col-span-2">
          <h3 className="text-sm font-semibold mb-4">Equity Curve</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={equityCurve}>
                <defs><linearGradient id="eqGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#00c48c" stopOpacity={0.2} /><stop offset="100%" stopColor="#00c48c" stopOpacity={0} /></linearGradient></defs>
                <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 10 }} />
                <YAxis domain={['auto', 'auto']} axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 10 }} />
                <Tooltip contentStyle={{ background: '#111827', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '8px', fontSize: '12px' }} />
                <Area type="monotone" dataKey="value" stroke="#00c48c" strokeWidth={2} fill="url(#eqGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>

        <GlassCard>
          <h3 className="text-sm font-semibold mb-4">Monthly P&L</h3>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={monthlyReturns}>
                <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 9 }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 9 }} />
                <Tooltip contentStyle={{ background: '#111827', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '8px', fontSize: '12px' }} />
                <Bar dataKey="pnl" fill="#00c48c" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>

        <GlassCard>
          <h3 className="text-sm font-semibold mb-4">Win / Loss</h3>
          <div className="h-48 flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={70} label={({ name, value }) => `${name} ${value.toFixed(0)}%`}>
                  {pieData.map((_, i) => <Cell key={i} fill={i === 0 ? '#00c48c' : '#ef4444'} />)}
                </Pie>
                <Tooltip contentStyle={{ background: '#111827', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '8px', fontSize: '12px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>
      </div>

      {stats?.by_symbol && Object.keys(stats.by_symbol).length > 0 && (
        <GlassCard>
          <h3 className="text-sm font-semibold mb-4">By Symbol</h3>
          <div className="grid grid-cols-4 gap-4">
            {Object.entries(stats.by_symbol).map(([sym, data]) => (
              <GlassCard key={sym}>
                <p className="text-sm font-semibold">{sym}</p>
                <p className="text-xs text-[var(--color-text-muted)]">{data.trades} trades</p>
                <p className="text-xs font-mono">${data.pnl.toFixed(2)}</p>
                <p className="text-xs" style={{ color: (data as { win_rate: number }).win_rate >= 50 ? '#00c48c' : '#ef4444' }}>{(data as { win_rate: number }).win_rate.toFixed(0)}% WR</p>
              </GlassCard>
            ))}
          </div>
        </GlassCard>
      )}
    </PageContainer>
  );
}
