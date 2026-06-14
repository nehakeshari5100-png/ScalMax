'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn, formatPrice, formatPercent } from '@/lib/utils';
import { PageContainer } from '@/components/layout/PageContainer';
import { GlassCard } from '@/components/ui/GlassCard';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { api } from '@/lib/api';
import {
  BookOpen, Search, Download, TrendingUp, TrendingDown, BarChart3, PieChart, Loader2, XCircle
} from 'lucide-react';
import type { Position } from '@/types/papertrading';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart as RePieChart, Pie, Cell
} from 'recharts';

const COLORS = ['#00c48c', '#ef4444', '#ff7c00', '#0040ff', '#8b5cf6'];

export default function JournalPage() {
  const [accountId, setAccountId] = useState<string | null>(null);
  const [trades, setTrades] = useState<Position[]>([]);
  const [stats, setStats] = useState<import('@/types/papertrading').PerformanceStats | null>(null);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedTrade, setSelectedTrade] = useState<Position | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const aid = await loadAccount();
      setAccountId(aid);
      if (!aid) { setError('No account'); setLoading(false); return; }

      const [posRes, statRes] = await Promise.all([
        api.listPaperPositions({ account_id: aid, limit: 200 }),
        api.getPaperStats(aid),
      ]);

      if (posRes.success) setTrades(posRes.data);
      if (statRes.success) setStats(statRes.data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load trades');
    } finally {
      setLoading(false);
    }
  }, [loadAccount]);

  useEffect(() => { load(); }, [load]);

  const filtered = trades.filter(t => {
    if (search && !t.symbol.toLowerCase().includes(search.toLowerCase())) return false;
    if (statusFilter !== 'all') {
      if (statusFilter === 'closed') return t.status === 'closed';
      if (statusFilter === 'open') return t.status === 'open';
      if (statusFilter === 'cancelled') return t.status === 'cancelled';
    }
    return true;
  }).sort((a, b) => b.opened_at - a.opened_at);

  const closedTrades = trades.filter(t => t.status === 'closed');
  const winRate = closedTrades.length > 0
    ? (closedTrades.filter(t => (t.pnl || 0) > 0).length / closedTrades.length * 100).toFixed(1)
    : '0';
  const totalPnl = closedTrades.reduce((sum, t) => sum + (t.pnl || 0), 0);

  const pnlBySymbol = trades.reduce((acc: Record<string, number>, t) => {
    if (t.pnl) acc[t.symbol] = (acc[t.symbol] || 0) + t.pnl;
    return acc;
  }, {});
  const pieData = Object.entries(pnlBySymbol).map(([name, value]) => ({ name: name.replace('USDT', ''), value: Math.abs(value) }));

  const formatTs = (ts: number) => new Date(ts * 1000).toLocaleDateString();

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

  return (
    <PageContainer>
      <div className="grid grid-cols-4 gap-4 mb-6">
        {[
          { label: 'Total Trades', value: trades.length.toString(), color: 'text-aurora-400' },
          { label: 'Win Rate', value: `${winRate}%`, color: 'text-aurora-400' },
          { label: 'Total P&L', value: `${totalPnl >= 0 ? '+' : ''}$${totalPnl.toFixed(2)}`, color: totalPnl >= 0 ? 'text-aurora-400' : 'text-red-400' },
          { label: 'Open Trades', value: trades.filter(t => t.status === 'open').length.toString(), color: 'text-cyber-400' },
        ].map((stat, i) => (
          <motion.div key={stat.label} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}>
            <GlassCard>
              <p className="stat-label">{stat.label}</p>
              <p className={cn('stat-value mt-1', stat.color)}>{stat.value}</p>
            </GlassCard>
          </motion.div>
        ))}
      </div>

      <div className="grid lg:grid-cols-2 gap-4 mb-6">
        <GlassCard>
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 className="w-4 h-4 text-aurora-400" />
            <h3 className="text-sm font-semibold">P&L Distribution by Symbol</h3>
          </div>
          <div className="h-48 flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <RePieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={4} dataKey="value">
                  {pieData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={{ background: '#111827', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '8px', fontSize: '12px' }} />
              </RePieChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>
        <GlassCard>
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-4 h-4 text-aurora-400" />
            <h3 className="text-sm font-semibold">Performance Summary</h3>
          </div>
          {stats && (
            <div className="grid grid-cols-2 gap-3">
              <div><p className="text-[10px] text-[var(--color-text-muted)]">Profit Factor</p><p className="text-sm font-mono">{(stats.profit_factor || 0).toFixed(2)}</p></div>
              <div><p className="text-[10px] text-[var(--color-text-muted)]">Avg Trade</p><p className="text-sm font-mono">${(stats.avg_pnl || 0).toFixed(2)}</p></div>
              <div><p className="text-[10px] text-[var(--color-text-muted)]">Max DD</p><p className="text-sm font-mono">{(stats.max_drawdown || 0).toFixed(1)}%</p></div>
              <div><p className="text-[10px] text-[var(--color-text-muted)]">Sharpe</p><p className="text-sm font-mono">{(stats.sharpe_ratio || 0).toFixed(2)}</p></div>
            </div>
          )}
        </GlassCard>
      </div>

      <GlassCard className="p-4 mb-6">
        <div className="flex items-center gap-4 flex-wrap">
          <div className="relative flex-1 min-w-[200px]">
            <input
              type="text"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search by symbol..."
              className="glass-input w-full pl-10 py-2 text-xs"
            />
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)]" />
          </div>
          <div className="flex items-center gap-1">
            {['all', 'open', 'closed', 'cancelled'].map(s => (
              <button key={s} onClick={() => setStatusFilter(s)}
                className={cn('px-3 py-1.5 text-xs rounded-lg capitalize transition-colors',
                  statusFilter === s ? 'bg-aurora-500/15 text-aurora-400' : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)] bg-surface-dark/40'
                )}>
                {s}
              </button>
            ))}
          </div>
          <span className="text-xs text-[var(--color-text-muted)]">{filtered.length} trades</span>
        </div>
      </GlassCard>

      <GlassCard className="p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/5">
                <th className="text-left text-[10px] font-medium text-[var(--color-text-muted)] uppercase px-4 py-3">Symbol</th>
                <th className="text-left text-[10px] font-medium text-[var(--color-text-muted)] uppercase px-4 py-3">Side</th>
                <th className="text-right text-[10px] font-medium text-[var(--color-text-muted)] uppercase px-4 py-3">Entry</th>
                <th className="text-right text-[10px] font-medium text-[var(--color-text-muted)] uppercase px-4 py-3">Exit</th>
                <th className="text-right text-[10px] font-medium text-[var(--color-text-muted)] uppercase px-4 py-3">P&L</th>
                <th className="text-left text-[10px] font-medium text-[var(--color-text-muted)] uppercase px-4 py-3">Status</th>
                <th className="text-left text-[10px] font-medium text-[var(--color-text-muted)] uppercase px-4 py-3">Date</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(t => (
                <tr key={t.id} onClick={() => setSelectedTrade(t)}
                  className={cn('border-b border-white/5 hover:bg-white/[0.02] cursor-pointer transition-colors',
                    selectedTrade?.id === t.id && 'bg-aurora-500/5'
                  )}>
                  <td className="px-4 py-3 text-sm font-semibold">{t.symbol.replace('USDT', '')}</td>
                  <td className="px-4 py-3">
                    <Badge variant={t.direction === 'long' ? 'long' : 'short'} size="sm">{t.direction.toUpperCase()}</Badge>
                  </td>
                  <td className="px-4 py-3 text-xs font-mono text-right">${formatPrice(t.entry_price)}</td>
                  <td className="px-4 py-3 text-xs font-mono text-right">{t.close_price ? `$${formatPrice(t.close_price)}` : '-'}</td>
                  <td className={cn('px-4 py-3 text-xs font-mono text-right font-medium',
                    (t.pnl || 0) >= 0 ? 'text-aurora-400' : 'text-red-400')}>
                    {(t.pnl || 0) >= 0 ? '+' : ''}${(t.pnl || 0).toFixed(2)}
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant={t.status === 'closed' ? 'success' : t.status === 'open' ? 'info' : 'neutral'} size="sm">{t.status}</Badge>
                  </td>
                  <td className="px-4 py-3 text-xs text-[var(--color-text-muted)]">{formatTs(t.opened_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {filtered.length === 0 && (
          <div className="flex items-center justify-center py-12 text-sm text-[var(--color-text-muted)]">No trades found</div>
        )}
      </GlassCard>

      <AnimatePresence>
        {selectedTrade && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 20 }} className="mt-6">
            <GlassCard className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <h3 className="text-base font-bold">{selectedTrade.symbol}</h3>
                  <Badge variant={selectedTrade.direction === 'long' ? 'long' : 'short'}>{selectedTrade.direction.toUpperCase()}</Badge>
                  <Badge variant={selectedTrade.status === 'closed' ? 'success' : selectedTrade.status === 'open' ? 'info' : 'neutral'}>{selectedTrade.status}</Badge>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div><div className="text-[10px] text-[var(--color-text-muted)] uppercase">Entry</div><div className="text-sm font-mono font-bold">${formatPrice(selectedTrade.entry_price)}</div></div>
                <div><div className="text-[10px] text-[var(--color-text-muted)] uppercase">Exit</div><div className="text-sm font-mono font-bold">{selectedTrade.close_price ? `$${formatPrice(selectedTrade.close_price)}` : '-'}</div></div>
                <div><div className="text-[10px] text-[var(--color-text-muted)] uppercase">Quantity</div><div className="text-sm font-mono font-bold">{selectedTrade.quantity}</div></div>
                <div><div className="text-[10px] text-[var(--color-text-muted)] uppercase">P&L</div><div className={cn('text-sm font-mono font-bold', (selectedTrade.pnl || 0) >= 0 ? 'text-aurora-400' : 'text-red-400')}>{(selectedTrade.pnl || 0) >= 0 ? '+' : ''}${(selectedTrade.pnl || 0).toFixed(2)}</div></div>
                <div><div className="text-[10px] text-[var(--color-text-muted)] uppercase">P&L%</div><div className={cn('text-sm font-mono font-bold', (selectedTrade.pnl_pct || 0) >= 0 ? 'text-aurora-400' : 'text-red-400')}>{(selectedTrade.pnl_pct || 0) >= 0 ? '+' : ''}{(selectedTrade.pnl_pct || 0).toFixed(2)}%</div></div>
                <div><div className="text-[10px] text-[var(--color-text-muted)] uppercase">Exit Reason</div><div className="text-sm font-mono font-bold">{selectedTrade.exit_reason || '-'}</div></div>
              </div>
            </GlassCard>
          </motion.div>
        )}
      </AnimatePresence>
    </PageContainer>
  );
}
