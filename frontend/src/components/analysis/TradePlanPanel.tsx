'use client';

import { useState, useEffect } from 'react';
import { cn, formatPrice } from '@/lib/utils';
import { GlassCard } from '@/components/ui/GlassCard';
import { Input } from '@/components/ui/Input';
import { Target, DollarSign, TrendingUp, TrendingDown } from 'lucide-react';
import type { TradePlan } from '@/types/vision';

interface TradePlanPanelProps {
  className?: string;
  analysis?: Pick<TradePlan, 'entry' | 'stop' | 'tp1' | 'tp2'> | null;
}

export function TradePlanPanel({ className, analysis }: TradePlanPanelProps) {
  const [capital, setCapital] = useState('10000');
  const [riskPercent, setRiskPercent] = useState('1.5');
  const [leverage, setLeverage] = useState('3');

  const extraction = analysis ? extractLevels(analysis) : null;
  const [entry, setEntry] = useState('');
  const [sl, setSl] = useState('');
  const [tp1, setTp1] = useState('');
  const [tp2, setTp2] = useState('');
  const [tp3, setTp3] = useState('');

  useEffect(() => {
    if (extraction) {
      setEntry(extraction.entry);
      setSl(extraction.sl);
      setTp1(extraction.tp1);
      setTp2(extraction.tp2);
      setTp3(extraction.tp3);
    }
  }, [extraction?.entry, extraction?.sl, extraction?.tp1, extraction?.tp2, extraction?.tp3]);

  const entryN = parseFloat(entry) || 0;
  const slN = parseFloat(sl) || 0;
  const tp1N = parseFloat(tp1) || 0;
  const tp2N = parseFloat(tp2) || 0;
  const tp3N = parseFloat(tp3) || 0;
  const capitalN = parseFloat(capital) || 10000;
  const riskPct = parseFloat(riskPercent) || 1.5;
  const levN = parseFloat(leverage) || 1;

  const isLong = entryN > slN;
  const riskAmount = capitalN * (riskPct / 100);
  const entryRiskPct = entryN ? Math.abs((entryN - slN) / entryN) * 100 : 0;
  const positionSize = entryRiskPct ? (riskAmount / (entryRiskPct / 100)) * levN : 0;
  const quantity = entryN ? positionSize / entryN : 0;

  const calcRR = (tp: number) => tp && entryN && slN ? (Math.abs(tp - entryN) / Math.abs(entryN - slN)).toFixed(2) : '-';
  const calcPnl = (tp: number) => tp && quantity ? Math.abs(tp - entryN) * quantity * levN : 0;

  const rr1 = calcRR(tp1N);
  const rr2 = calcRR(tp2N);
  const rr3 = calcRR(tp3N);
  const pnl1 = calcPnl(tp1N);
  const pnl2 = calcPnl(tp2N);
  const pnl3 = calcPnl(tp3N);
  const totalPnl = pnl1 + pnl2 + pnl3;

  const isAutoFilled = !!extraction;
  const hasValues = entryN > 0 && slN > 0;

  return (
    <GlassCard className={cn('space-y-4', className)} glow="blue">
      <div className="flex items-center gap-2 pb-3 border-b border-white/5">
        <Target className="w-4 h-4 text-cyber-400" />
        <h3 className="text-sm font-semibold">Trade Plan</h3>
        {isAutoFilled && <span className="text-[10px] text-aurora-400 ml-auto">Auto-filled from analysis</span>}
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Input label="Entry Price" value={entry} onChange={e => setEntry(e.target.value)} placeholder="67542" />
        <Input label="Stop Loss" value={sl} onChange={e => setSl(e.target.value)} placeholder="67100" />
        <Input label="Take Profit 1" value={tp1} onChange={e => setTp1(e.target.value)} placeholder="68200" />
        <Input label="Take Profit 2" value={tp2} onChange={e => setTp2(e.target.value)} placeholder="68700" />
        <Input label="Take Profit 3" value={tp3} onChange={e => setTp3(e.target.value)} placeholder="69200" />
        <Input label="Account Capital" value={capital} onChange={e => setCapital(e.target.value)} placeholder="10000" />
        <Input label="Risk %" value={riskPercent} onChange={e => setRiskPercent(e.target.value)} placeholder="1.5" />
        <Input label="Leverage" value={leverage} onChange={e => setLeverage(e.target.value)} placeholder="3" />
      </div>

      {hasValues && (
        <div className="glass-card p-4 space-y-3">
          <div className="text-xs font-medium text-aurora-400 uppercase tracking-wider flex items-center gap-1.5">
            <DollarSign className="w-3 h-3" />
            Position Summary
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
            <ResultItem label="Risk Amount" value={`$${(riskAmount ?? 0).toFixed(2)}`} />
            <ResultItem label="Entry Risk" value={`${(entryRiskPct ?? 0).toFixed(2)}%`} />
            <ResultItem label="Position Size" value={`$${(positionSize ?? 0).toFixed(2)}`} />
            <ResultItem label="Quantity" value={(quantity ?? 0).toFixed(quantity < 1 ? 4 : 2)} />
            <ResultItem label="Direction" value={isLong ? 'LONG' : 'SHORT'} color={isLong ? 'aurora' : 'red'} />
          </div>

          <div className="pt-3 border-t border-white/5">
            <div className="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider mb-3">Take Profit Targets</div>
            <div className="grid grid-cols-3 gap-4">
              <TpCard label="TP 1" price={tp1N} rr={rr1} pnl={pnl1} isLong={isLong} />
              <TpCard label="TP 2" price={tp2N} rr={rr2} pnl={pnl2} isLong={isLong} />
              <TpCard label="TP 3" price={tp3N} rr={rr3} pnl={pnl3} isLong={isLong} />
            </div>
            {totalPnl > 0 && (
              <div className="mt-3 pt-3 border-t border-white/5 flex items-center justify-between">
                <span className="text-xs text-[var(--color-text-muted)]">Total Expected Profit</span>
                <span className="text-sm font-bold font-mono text-aurora-400">
                  ${totalPnl.toFixed(2)} ({(totalPnl / capitalN * 100).toFixed(2)}% gain)
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </GlassCard>
  );
}

function TpCard({ label, price, rr, pnl, isLong }: { label: string; price: number; rr: string; pnl: number; isLong: boolean }) {
  if (!price) return null;
  return (
    <div className="p-3 rounded-lg bg-surface-elevated/40 border border-white/5">
      <div className="text-[10px] text-[var(--color-text-muted)] uppercase">{label}</div>
      <div className="text-sm font-bold font-mono mt-0.5">{price}</div>
      <div className="flex items-center justify-between mt-2">
        <span className="text-[10px] text-[var(--color-text-muted)]">R:R 1:{rr}</span>
        <span className={cn('text-xs font-bold font-mono', isLong ? 'text-aurora-400' : 'text-red-400')}>
          ${(pnl ?? 0).toFixed(0)}
        </span>
      </div>
    </div>
  );
}

function ResultItem({ label, value, color = 'default' }: { label: string; value: string; color?: string }) {
  return (
    <div>
      <div className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider">{label}</div>
      <div className={cn(
        'text-sm font-bold font-mono',
        color === 'aurora' ? 'text-aurora-400' : color === 'red' ? 'text-red-400' : 'text-[var(--color-text)]'
      )}>
        {value}
      </div>
    </div>
  );
}

function extractLevels(analysis: NonNullable<TradePlanPanelProps['analysis']>) {
  const parsePrice = (s: string) => {
    const m = s.match(/[\d,.]+/);
    return m ? m[0].replace(/,/g, '') : '';
  };
  const entryPrice = parsePrice(analysis.entry);
  const slPrice = parsePrice(analysis.stop);
  const tp1Price = parsePrice(analysis.tp1);
  const tp2Price = parsePrice(analysis.tp2);
  if (!entryPrice || !slPrice) return null;
  return { entry: entryPrice, sl: slPrice, tp1: tp1Price, tp2: tp2Price, tp3: '' };
}
