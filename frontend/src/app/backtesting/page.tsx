'use client';

import { useState, useEffect, useCallback } from 'react';
import { cn } from '@/lib/utils';
import { PageContainer } from '@/components/layout/PageContainer';
import { GlassCard } from '@/components/ui/GlassCard';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { api } from '@/lib/api';
import {
  FlaskConical, Play, BarChart3, Target, Settings, RotateCcw, XCircle, RefreshCw
} from 'lucide-react';
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell
} from 'recharts';
import type { BacktestResult } from '@/types/backtesting';

const symbols = [
  { value: 'BTCUSDT', label: 'BTC/USDT' },
  { value: 'ETHUSDT', label: 'ETH/USDT' },
  { value: 'SOLUSDT', label: 'SOL/USDT' },
  { value: 'BNBUSDT', label: 'BNB/USDT' },
];

const timeframes = [
  { value: '1m', label: '1m' },
  { value: '3m', label: '3m' },
  { value: '5m', label: '5m' },
  { value: '15m', label: '15m' },
  { value: '30m', label: '30m' },
  { value: '1h', label: '1h' },
];

export default function BacktestingPage() {
  const [results, setResults] = useState<BacktestResult[]>([]);
  const [selectedResult, setSelectedResult] = useState<BacktestResult | null>(null);
  const [running, setRunning] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Config state
  const [config, setConfig] = useState({
    symbol: 'BTCUSDT',
    timeframe: '5m',
    startDate: '2026-05-01',
    endDate: '2026-06-01',
    initialCapital: '10000',
    riskPerTrade: '1.5',
    maxLeverage: '5',
  });

  const loadResults = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getBacktestResults({ limit: 20 });
      if (res.success) {
        setResults(res.data);
        if (res.data.length > 0 && !selectedResult) setSelectedResult(res.data[0]);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load results');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadResults(); }, [loadResults]);

  const runSimulation = async () => {
    setRunning(true);
    setError(null);
    try {
      const res = await api.runBacktest({
        symbol: config.symbol,
        timeframe: config.timeframe,
        start_date: config.startDate || null,
        end_date: config.endDate || null,
        initial_capital: parseFloat(config.initialCapital) || 10000,
        risk_per_trade_pct: parseFloat(config.riskPerTrade) || 1.5,
      });
      if (res.success && res.data) {
        setSelectedResult(res.data);
        setResults(prev => [res.data!, ...prev]);
      } else {
        setError(res.error || 'Backtest failed');
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Backtest failed');
    } finally {
      setRunning(false);
    }
  };

  return (
    <PageContainer>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-amber-700 flex items-center justify-center">
            <FlaskConical className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-bold">Backtesting Engine</h2>
            <p className="text-xs text-[var(--color-text-muted)]">Historical strategy simulation and optimization</p>
          </div>
        </div>
        <Button variant="outline" size="sm" onClick={loadResults}>
          <RefreshCw className="w-3 h-3 mr-1" /> Refresh
        </Button>
      </div>

      {error && (
        <div className="flex items-center gap-2 px-4 py-2 mb-4 rounded-lg bg-red-500/10 border border-red-500/20 text-xs text-red-400">
          <XCircle className="w-3 h-3" /> {error}
        </div>
      )}

      <div className="grid lg:grid-cols-4 gap-6">
        <div className="space-y-4">
          <GlassCard className="p-5 space-y-4">
            <h3 className="text-sm font-semibold flex items-center gap-2">
              <Settings className="w-4 h-4 text-amber-400" /> Parameters
            </h3>
            <Select label="Symbol" options={symbols} value={config.symbol} onChange={e => setConfig(p => ({ ...p, symbol: e.target.value }))} />
            <Select label="Timeframe" options={timeframes} value={config.timeframe} onChange={e => setConfig(p => ({ ...p, timeframe: e.target.value }))} />
            <Input label="Start Date" type="date" value={config.startDate} onChange={e => setConfig(p => ({ ...p, startDate: e.target.value }))} />
            <Input label="End Date" type="date" value={config.endDate} onChange={e => setConfig(p => ({ ...p, endDate: e.target.value }))} />
            <Input label="Initial Capital ($)" value={config.initialCapital} onChange={e => setConfig(p => ({ ...p, initialCapital: e.target.value }))} />
            <Input label="Risk Per Trade (%)" value={config.riskPerTrade} onChange={e => setConfig(p => ({ ...p, riskPerTrade: e.target.value }))} />
            <Input label="Max Leverage" value={config.maxLeverage} onChange={e => setConfig(p => ({ ...p, maxLeverage: e.target.value }))} />
            <div className="pt-2">
              <Button variant="primary" className="w-full" size="lg"
                icon={running ? <RotateCcw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                onClick={runSimulation} loading={running}>
                {running ? 'Running...' : 'Run Backtest'}
              </Button>
            </div>
          </GlassCard>

          {results.length > 0 && (
            <GlassCard className="p-5">
              <h3 className="text-sm font-semibold mb-3">Saved Results</h3>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {results.map(r => (
                  <div key={r.id || Math.random()}
                    className={cn('px-3 py-2 rounded-lg text-xs cursor-pointer transition-colors',
                      selectedResult?.id === r.id ? 'bg-aurora-500/10 text-aurora-400 border border-aurora-500/20' : 'hover:bg-white/[0.03] border border-transparent'
                    )}
                    onClick={() => setSelectedResult(r)}>
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{r.config.symbol} ({r.config.timeframe})</span>
                      <span className={r.metrics.net_profit_pct >= 0 ? 'text-aurora-400' : 'text-red-400'}>
                        {r.metrics.net_profit_pct >= 0 ? '+' : ''}{r.metrics.net_profit_pct.toFixed(2)}%
                      </span>
                    </div>
                    <div className="text-[10px] text-[var(--color-text-muted)] mt-0.5">
                      {r.config.start_date || 'N/A'} - {r.config.end_date || 'N/A'} | {r.metrics.total_trades} trades
                    </div>
                  </div>
                ))}
              </div>
            </GlassCard>
          )}
        </div>

        <div className="lg:col-span-3 space-y-6">
          {selectedResult ? (
            <>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                {[
                  { label: 'Total Return', value: `${selectedResult.metrics.net_profit_pct >= 0 ? '+' : ''}${selectedResult.metrics.net_profit_pct.toFixed(2)}%`, color: selectedResult.metrics.net_profit_pct >= 0 ? 'text-aurora-400' : 'text-red-400' },
                  { label: 'Total Trades', value: selectedResult.metrics.total_trades.toString(), color: 'text-[var(--color-text)]' },
                  { label: 'Win Rate', value: `${(selectedResult.metrics.win_rate || 0).toFixed(1)}%`, color: selectedResult.metrics.win_rate >= 50 ? 'text-aurora-400' : 'text-red-400' },
                  { label: 'Profit Factor', value: (selectedResult.metrics.profit_factor || 0).toFixed(2), color: selectedResult.metrics.profit_factor >= 1.5 ? 'text-aurora-400' : 'text-ember-400' },
                  { label: 'Sharpe', value: (selectedResult.metrics.sharpe_ratio || 0).toFixed(2), color: selectedResult.metrics.sharpe_ratio >= 1.5 ? 'text-aurora-400' : 'text-ember-400' },
                  { label: 'Sortino', value: (selectedResult.metrics.sortino_ratio || 0).toFixed(2), color: selectedResult.metrics.sortino_ratio >= 2 ? 'text-aurora-400' : 'text-ember-400' },
                  { label: 'Max DD', value: `${(selectedResult.metrics.max_drawdown_pct || 0).toFixed(2)}%`, color: selectedResult.metrics.max_drawdown_pct <= 10 ? 'text-aurora-400' : 'text-red-400' },
                  { label: 'Net Profit', value: `$${(selectedResult.metrics.net_profit || 0).toFixed(2)}`, color: selectedResult.metrics.net_profit >= 0 ? 'text-aurora-400' : 'text-red-400' },
                ].map((stat, i) => (
                  <GlassCard key={stat.label}>
                    <p className="stat-label">{stat.label}</p>
                    <p className={cn('stat-value mt-1', stat.color)}>{stat.value}</p>
                  </GlassCard>
                ))}
              </div>

              {selectedResult.equity_curve && selectedResult.equity_curve.length > 0 && (
                <GlassCard>
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <BarChart3 className="w-4 h-4 text-aurora-400" />
                      <h3 className="text-sm font-semibold">Equity Curve</h3>
                    </div>
                    <div className="flex items-center gap-1 text-xs">
                      <Badge variant="success">+{selectedResult.metrics.net_profit_pct.toFixed(2)}%</Badge>
                      <Badge variant="info">Sharpe {selectedResult.metrics.sharpe_ratio?.toFixed(2) || 'N/A'}</Badge>
                    </div>
                  </div>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={selectedResult.equity_curve.map(p => ({ date: new Date(p.timestamp * 1000).toLocaleDateString(), value: p.equity }))}>
                        <defs><linearGradient id="eqGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#00c48c" stopOpacity={0.2} /><stop offset="100%" stopColor="#00c48c" stopOpacity={0} /></linearGradient></defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
                        <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 10 }} />
                        <YAxis domain={['auto', 'auto']} axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 10 }} />
                        <Tooltip contentStyle={{ background: '#111827', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '8px', fontSize: '12px' }} />
                        <Area type="monotone" dataKey="value" stroke="#00c48c" strokeWidth={2} fill="url(#eqGrad)" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </GlassCard>
              )}

              {selectedResult.monthly && selectedResult.monthly.length > 0 && (
                <GlassCard>
                  <div className="flex items-center gap-2 mb-4">
                    <BarChart3 className="w-4 h-4 text-cyber-400" />
                    <h3 className="text-sm font-semibold">Monthly Returns</h3>
                  </div>
                  <div className="h-48">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={selectedResult.monthly.map(m => ({ month: `${m.year}-${String(m.month).padStart(2, '0')}`, pnl: m.net_pnl }))}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
                        <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 10 }} />
                        <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 10 }} />
                        <Tooltip contentStyle={{ background: '#111827', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '8px', fontSize: '12px' }} />
                        <Bar dataKey="pnl" radius={[4, 4, 0, 0]}>
                          {selectedResult.monthly.map((m, i) => <Cell key={i} fill={m.net_pnl >= 0 ? '#00c48c' : '#ef4444'} />)}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </GlassCard>
              )}

              <div className="grid lg:grid-cols-2 gap-6">
                <GlassCard>
                  <div className="flex items-center gap-2 mb-4">
                    <Target className="w-4 h-4 text-amber-400" />
                    <h3 className="text-sm font-semibold">Metrics Summary</h3>
                  </div>
                  <div className="space-y-3">
                    {[
                      ['Total Trades', selectedResult.metrics.total_trades],
                      ['Win / Loss / BE', `${selectedResult.metrics.wins} / ${selectedResult.metrics.losses} / ${selectedResult.metrics.break_even || 0}`],
                      ['Win Rate', `${(selectedResult.metrics.win_rate || 0).toFixed(1)}%`],
                      ['Avg R Multiple', (selectedResult.metrics.avg_r_multiple || 0).toFixed(2)],
                      ['Avg Win / Loss', `$${(selectedResult.metrics.avg_win_pct || 0).toFixed(2)} / $${(selectedResult.metrics.avg_loss_pct || 0).toFixed(2)}`],
                      ['Max Drawdown', `${(selectedResult.metrics.max_drawdown_pct || 0).toFixed(2)}%`],
                      ['Expectancy', `$${(selectedResult.metrics.expectancy || 0).toFixed(2)}`],
                      ['Total Fees', `$${(selectedResult.metrics.total_fees || 0).toFixed(2)}`],
                    ].map(([label, value]) => (
                      <div key={label as string} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
                        <span className="text-sm text-[var(--color-text-secondary)]">{label as string}</span>
                        <span className="text-sm font-mono font-medium">{String(value)}</span>
                      </div>
                    ))}
                  </div>
                </GlassCard>

                <GlassCard>
                  <div className="flex items-center gap-2 mb-4">
                    <Settings className="w-4 h-4 text-amber-400" />
                    <h3 className="text-sm font-semibold">Config</h3>
                  </div>
                  <div className="space-y-3">
                    {Object.entries(selectedResult.config).map(([key, value]) => (
                      <div key={key} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
                        <span className="text-sm text-[var(--color-text-secondary)] capitalize">
                          {key.replace(/_/g, ' ').replace(/([a-z])([A-Z])/g, '$1 $2')}
                        </span>
                        <span className="text-sm font-mono font-medium">{String(value)}</span>
                      </div>
                    ))}
                  </div>
                </GlassCard>
              </div>
            </>
          ) : (
            <GlassCard className="flex items-center justify-center py-20 text-center">
              <FlaskConical className="w-12 h-12 text-[var(--color-text-muted)] mb-3" />
              <p className="text-sm text-[var(--color-text-muted)]">Configure and run a backtest</p>
              <p className="text-xs text-[var(--color-text-muted)] mt-1">Select parameters on the left and press Run Backtest</p>
            </GlassCard>
          )}
        </div>
      </div>
    </PageContainer>
  );
}
