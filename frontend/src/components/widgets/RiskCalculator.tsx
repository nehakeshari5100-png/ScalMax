'use client';

import { useState } from 'react';
import { cn, formatPrice } from '@/lib/utils';
import { GlassCard } from '@/components/ui/GlassCard';
import { Input } from '@/components/ui/Input';
import { Shield } from 'lucide-react';

interface RiskCalculatorProps {
  className?: string;
  entry?: number;
  stopLoss?: number;
}

export function RiskCalculator({ className, entry: defaultEntry, stopLoss: defaultSl }: RiskCalculatorProps) {
  const [entry, setEntry] = useState(defaultEntry?.toString() || '');
  const [sl, setSl] = useState(defaultSl?.toString() || '');
  const [tp1, setTp1] = useState('');
  const [tp2, setTp2] = useState('');
  const [capital, setCapital] = useState('10000');
  const [riskPercent, setRiskPercent] = useState('1.5');
  const [leverage, setLeverage] = useState('3');

  const entryN = parseFloat(entry) || 0;
  const slN = parseFloat(sl) || 0;
  const tp1N = parseFloat(tp1) || 0;
  const tp2N = parseFloat(tp2) || 0;
  const capitalN = parseFloat(capital) || 10000;
  const riskPct = parseFloat(riskPercent) || 1.5;
  const levN = parseFloat(leverage) || 1;

  const isLong = entryN > slN;
  const riskAmount = capitalN * (riskPct / 100);
  const entryRiskPct = entryN ? Math.abs((entryN - slN) / entryN) * 100 : 0;
  const positionSize = entryRiskPct ? (riskAmount / (entryRiskPct / 100)) * levN : 0;
  const quantity = entryN ? positionSize / entryN : 0;
  const rr1 = tp1N ? (Math.abs(tp1N - entryN) / Math.abs(entryN - slN)).toFixed(2) : '-';
  const rr2 = tp2N ? (Math.abs(tp2N - entryN) / Math.abs(entryN - slN)).toFixed(2) : '-';
  const tp1Pnl = tp1N && quantity ? (Math.abs(tp1N - entryN) * quantity * levN) : 0;
  const tp2Pnl = tp2N && quantity ? (Math.abs(tp2N - entryN) * quantity * levN) : 0;

  return (
    <GlassCard className={cn('space-y-4', className)} glow="blue">
      <div className="flex items-center gap-2">
        <Shield className="w-4 h-4 text-cyber-400" />
        <h3 className="text-sm font-semibold">Risk Calculator</h3>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <Input label="Entry Price" value={entry} onChange={e => setEntry(e.target.value)} placeholder="67542" />
        <Input label="Stop Loss" value={sl} onChange={e => setSl(e.target.value)} placeholder="67100" />
        <Input label="Take Profit 1" value={tp1} onChange={e => setTp1(e.target.value)} placeholder="68200" />
        <Input label="Take Profit 2" value={tp2} onChange={e => setTp2(e.target.value)} placeholder="68700" />
        <Input label="Account Capital" value={capital} onChange={e => setCapital(e.target.value)} placeholder="10000" />
        <Input label="Risk %" value={riskPercent} onChange={e => setRiskPercent(e.target.value)} placeholder="1.5" />
        <Input label="Leverage" value={leverage} onChange={e => setLeverage(e.target.value)} placeholder="3" />
      </div>

      {entryN > 0 && slN > 0 && (
        <div className="glass-card p-4 space-y-3 border-aurora-500/10">
          <div className="text-xs font-medium text-aurora-400 uppercase tracking-wider">Results</div>
          <div className="grid grid-cols-2 gap-4">
            <ResultItem label="Risk Amount" value={`$${riskAmount.toFixed(2)}`} />
            <ResultItem label="Entry Risk" value={`${entryRiskPct.toFixed(2)}%`} />
            <ResultItem label="Position Size" value={`$${positionSize.toFixed(2)}`} />
            <ResultItem label="Quantity" value={quantity.toFixed(quantity < 1 ? 4 : 2)} />
            <ResultItem label="R:R (TP1)" value={`1:${rr1}`} />
            <ResultItem label="R:R (TP2)" value={`1:${rr2}`} />
            <ResultItem label="TP1 PnL" value={`$${tp1Pnl.toFixed(2)}`} color="aurora" />
            <ResultItem label="TP2 PnL" value={`$${tp2Pnl.toFixed(2)}`} color="aurora" />
          </div>
        </div>
      )}
    </GlassCard>
  );
}

function ResultItem({ label, value, color = 'default' }: { label: string; value: string; color?: string }) {
  return (
    <div>
      <div className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider">{label}</div>
      <div className={cn(
        'text-sm font-bold font-mono',
        color === 'aurora' ? 'text-aurora-400' : 'text-[var(--color-text)]'
      )}>
        {value}
      </div>
    </div>
  );
}
