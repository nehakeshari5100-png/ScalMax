'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import { GlassCard } from '@/components/ui/GlassCard';
import { TrendingUp, TrendingDown, DollarSign, PieChart, Target, Activity } from 'lucide-react';
import { api } from '@/lib/api';
import type { VirtualAccount } from '@/types/papertrading';

interface PortfolioStatsProps {
  accountId?: string | null;
  className?: string;
}

export function PortfolioStats({ accountId, className }: PortfolioStatsProps) {
  const [acct, setAcct] = useState<VirtualAccount | null>(null);

  useEffect(() => {
    if (!accountId) return;
    api.getPaperAccount(accountId).then(r => {
      if (r.success && r.data) setAcct(r.data);
    }).catch(() => {});
  }, [accountId]);

  if (!acct) {
    return (
      <div className={cn('grid grid-cols-2 lg:grid-cols-4 gap-4', className)}>
        {['Total Equity', 'Daily P&L', 'Win Rate', 'Profit Factor'].map(label => (
          <GlassCard key={label}>
            <p className="stat-label">{label}</p>
            <p className="text-lg font-bold font-mono text-[var(--color-text-muted)]">---</p>
          </GlassCard>
        ))}
      </div>
    );
  }

  const mainStats = [
    { label: 'Total Equity', value: `$${acct.current_balance.toLocaleString()}`, change: `${acct.total_pnl_pct >= 0 ? '+' : ''}${(acct.total_pnl_pct ?? 0).toFixed(2)}%`, positive: acct.total_pnl_pct >= 0, icon: DollarSign },
    { label: 'Total P&L', value: `${acct.total_pnl >= 0 ? '+' : ''}$${(acct.total_pnl ?? 0).toFixed(2)}`, change: '', positive: acct.total_pnl >= 0, icon: TrendingUp },
    { label: 'Net Change', value: `${acct.total_pnl_pct >= 0 ? '+' : ''}${(acct.total_pnl_pct ?? 0).toFixed(2)}%`, change: '', positive: acct.total_pnl_pct >= 0, icon: Activity },
    { label: 'Initial Balance', value: `$${acct.initial_balance.toLocaleString()}`, change: '', positive: true, icon: Target },
  ];

  return (
    <div className={cn('grid grid-cols-2 lg:grid-cols-4 gap-4', className)}>
      {mainStats.map((stat, i) => {
        const Icon = stat.icon;
        return (
          <motion.div key={stat.label} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}>
            <GlassCard className="relative overflow-hidden">
              <div className="flex items-start justify-between">
                <div>
                  <p className="stat-label">{stat.label}</p>
                  <p className={cn('stat-value mt-1', stat.positive ? 'text-aurora-400' : 'text-red-400')}>{stat.value}</p>
                  {stat.change && <p className={cn('text-xs mt-0.5', stat.positive ? 'text-aurora-400' : 'text-red-400')}>{stat.change}</p>}
                </div>
                <div className={cn('w-9 h-9 rounded-lg flex items-center justify-center', stat.positive ? 'bg-aurora-500/10' : 'bg-red-500/10')}>
                  <Icon className={cn('w-4 h-4', stat.positive ? 'text-aurora-400' : 'text-red-400')} />
                </div>
              </div>
              <div className={cn('absolute bottom-0 left-0 right-0 h-0.5', stat.positive ? 'bg-gradient-to-r from-aurora-500/30 to-transparent' : 'bg-gradient-to-r from-red-500/30 to-transparent')} />
            </GlassCard>
          </motion.div>
        );
      })}
    </div>
  );
}

export function PortfolioEquity({ accountId, className }: { accountId?: string | null; className?: string }) {
  const [acct, setAcct] = useState<VirtualAccount | null>(null);

  useEffect(() => {
    if (!accountId) return;
    api.getPaperAccount(accountId).then(r => {
      if (r.success && r.data) setAcct(r.data);
    }).catch(() => {});
  }, [accountId]);

  if (!acct) return null;

  return (
    <GlassCard className={className}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <PieChart className="w-4 h-4 text-aurora-400" />
          <h3 className="text-sm font-semibold">Portfolio Overview</h3>
        </div>
      </div>
      <div className="grid grid-cols-3 gap-6">
        <div className="space-y-1">
          <p className="stat-label">Current Balance</p>
          <p className="text-lg font-bold font-mono">${acct.current_balance.toLocaleString()}</p>
        </div>
        <div className="space-y-1">
          <p className="stat-label">Total P&L</p>
          <p className={cn('text-lg font-bold font-mono', acct.total_pnl >= 0 ? 'text-aurora-400' : 'text-red-400')}>
            {acct.total_pnl >= 0 ? '+' : ''}${(acct.total_pnl ?? 0).toFixed(2)}
          </p>
        </div>
        <div className="space-y-1">
          <p className="stat-label">Total P&L%</p>
          <p className={cn('text-lg font-bold font-mono', acct.total_pnl_pct >= 0 ? 'text-aurora-400' : 'text-red-400')}>
            {acct.total_pnl_pct >= 0 ? '+' : ''}{(acct.total_pnl_pct ?? 0).toFixed(2)}%
          </p>
        </div>
      </div>
    </GlassCard>
  );
}
