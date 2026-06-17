'use client';

import { motion } from 'framer-motion';
import { useMemo, memo } from 'react';
import { cn } from '@/lib/utils';
import { GlassCard } from '@/components/ui/GlassCard';
import {
  TrendingUp, TrendingDown, Minus, Shield, Target,
  Zap, BarChart3, Eye, Activity,
  Layers,
} from 'lucide-react';
import type { MarketExtraction, ValidationReport } from '@/types/vision';
import { ValidationReportCard } from '@/components/analysis/ValidationReport';
import { InstitutionalResult } from '@/components/analysis/InstitutionalResult';

interface AnalysisResultProps {
  extraction: MarketExtraction;
  validation: ValidationReport | null;
}

const BIAS_CONFIG: Record<string, { icon: any; color: string; bg: string; border: string; label: string }> = {
  LONG: { icon: TrendingUp, color: 'text-aurora-500', bg: 'bg-aurora-500/10', border: 'border-aurora-500/15', label: 'LONG' },
  SHORT: { icon: TrendingDown, color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/15', label: 'SHORT' },
  NO_TRADE: { icon: Minus, color: 'text-ember-400', bg: 'bg-ember-500/10', border: 'border-ember-500/20', label: 'NO TRADE' },
};

function Tag({ children, color }: { children: React.ReactNode; color?: string }) {
  return (
    <span className={cn(
      'inline-flex px-2 py-0.5 rounded text-[10px] font-medium',
      color === 'green' && 'bg-aurora-500/10 text-aurora-400',
      color === 'red' && 'bg-red-500/10 text-red-400',
      color === 'amber' && 'bg-ember-500/10 text-ember-400',
      color === 'blue' && 'bg-cyber-500/10 text-cyber-400',
      !color && 'bg-surface-elevated/60 text-[var(--color-text-muted)]',
    )}>{children}</span>
  );
}

const ScoringBars = memo(function ScoringBars({ scoring }: { scoring: { marketStructure: number; liquidity: number; fvg: number; orderBlocks: number; volume: number; momentum: number; total: number } }) {
  return (
    <div className="space-y-2">
      {[
        { label: 'Market Structure', value: scoring.marketStructure, weight: '25%', color: 'bg-cyber-400' },
        { label: 'Liquidity', value: scoring.liquidity, weight: '20%', color: 'bg-aurora-400' },
        { label: 'FVG', value: scoring.fvg, weight: '15%', color: 'bg-amber-400' },
        { label: 'Order Blocks', value: scoring.orderBlocks, weight: '15%', color: 'bg-blue-400' },
        { label: 'Volume', value: scoring.volume, weight: '15%', color: 'bg-purple-400' },
        { label: 'Momentum', value: scoring.momentum, weight: '10%', color: 'bg-pink-400' },
      ].map((item) => (
        <div key={item.label} className="flex items-center gap-3">
          <span className="text-[10px] text-[var(--color-text-muted)] w-28 shrink-0">{item.label} <span className="text-[9px]">({item.weight})</span></span>
          <div className="flex-1 h-1.5 rounded-full bg-white/5 overflow-hidden">
            <div className={cn('h-full rounded-full', item.color)} style={{ width: `${item.value}%` }} />
          </div>
          <span className="text-[10px] font-mono text-[var(--color-text-muted)] w-8 text-right">{item.value}</span>
        </div>
      ))}
    </div>
  );
});

export const AnalysisResult = memo(function AnalysisResult({ extraction, validation }: AnalysisResultProps) {
  const cd = extraction?.chartDetection || {} as MarketExtraction['chartDetection'];
  const ms = extraction?.marketStructure || {} as MarketExtraction['marketStructure'];
  const liq = extraction?.liquidity || {} as MarketExtraction['liquidity'];
  const smc = extraction?.smc || {} as MarketExtraction['smc'];
  const fvgs = extraction?.fvgs || [];
  const obs = extraction?.orderBlocks || [];
  const pd = extraction?.premiumDiscount || {} as MarketExtraction['premiumDiscount'];
  const vol = extraction?.volume || {} as MarketExtraction['volume'];
  const mom = extraction?.momentum || {} as MarketExtraction['momentum'];
  const trade = extraction?.trade || {} as MarketExtraction['trade'];
  const scoring = extraction?.scoring || {} as MarketExtraction['scoring'];

  const cfg = BIAS_CONFIG[trade?.bias] || BIAS_CONFIG.NO_TRADE;
  const VerdictIcon = cfg.icon;

  const confidenceColor = useMemo(() => (trade?.confidence || 0) >= 85 ? 'bg-aurora-400' : (trade?.confidence || 0) >= 70 ? 'bg-cyber-400' : 'bg-ember-400', [trade?.confidence]);

  const hasInstitutional = !!(extraction?.institutionalDecision && extraction.institutionalDecision.marketState);

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
      {hasInstitutional ? (
        <InstitutionalResult extraction={extraction} inst={extraction.institutionalDecision!} />
      ) : (
        <>
      {/* Header */}
      <div className="flex items-center gap-2">
        <Layers className="w-5 h-5 text-cyber-400" />
        <h2 className="text-base font-bold">12-Step Extraction</h2>
      </div>

      {/* Trade Verdict */}
      <GlassCard className={cn('p-5 border', cfg.border)}>
        <div className="flex items-center gap-4">
          <div className={cn('w-14 h-14 rounded-2xl flex items-center justify-center', cfg.bg)}>
            <VerdictIcon className={cn('w-7 h-7', cfg.color)} />
          </div>
          <div className="flex-1">
            <p className={cn('text-lg font-bold', cfg.color)}>{cfg.label}</p>
            <p className="text-xs text-[var(--color-text-muted)] mt-0.5">Engine Decision</p>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-2">
              <div className="w-20 h-2 rounded-full bg-white/5 overflow-hidden">
                <div className={cn('h-full rounded-full transition-all', confidenceColor)} style={{ width: `${trade.confidence}%` }} />
              </div>
              <span className={cn('text-sm font-bold font-mono', confidenceColor.replace('bg-', 'text-'))}>{trade.confidence}%</span>
            </div>
            <p className="text-[10px] text-[var(--color-text-muted)] mt-0.5">Confidence</p>
          </div>
        </div>
        {trade.reasoning.length > 0 && (
          <div className="mt-3 pt-3 border-t border-white/5 space-y-1">
            {trade.reasoning.map((r, i) => (
              <p key={i} className="text-[11px] text-[var(--color-text-muted)] pl-3 border-l-2 border-cyber-500/30">{r}</p>
            ))}
          </div>
        )}
      </GlassCard>

      {/* STEP 1: Chart Detection */}
      <GlassCard className="p-4">
        <div className="flex items-center gap-2 mb-3">
          <Eye className="w-4 h-4 text-cyber-400" />
          <h3 className="text-sm font-semibold">Chart Detection</h3>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-4 gap-y-2">
          {cd.symbol && <div><span className="text-[10px] text-[var(--color-text-muted)]">Symbol <Tag color={cd.symbolConfidence >= 80 ? 'green' : 'amber'}>{cd.symbolConfidence}%</Tag></span><p className="text-xs font-mono font-medium">{cd.symbol}</p></div>}
          {cd.timeframe && <div><span className="text-[10px] text-[var(--color-text-muted)]">Timeframe <Tag color={cd.timeframeConfidence >= 80 ? 'green' : 'amber'}>{cd.timeframeConfidence}%</Tag></span><p className="text-xs font-mono font-medium">{cd.timeframe}</p></div>}
          {cd.currentPrice && <div><span className="text-[10px] text-[var(--color-text-muted)]">Price <Tag color={cd.priceConfidence >= 80 ? 'green' : 'amber'}>{cd.priceConfidence}%</Tag></span><p className="text-xs font-mono font-medium text-aurora-400">{cd.currentPrice}</p></div>}
          {cd.exchange && <div><span className="text-[10px] text-[var(--color-text-muted)]">Exchange <Tag color={cd.exchangeConfidence >= 80 ? 'green' : 'amber'}>{cd.exchangeConfidence}%</Tag></span><p className="text-xs font-mono">{cd.exchange}</p></div>}
          {cd.sessionType && <div><span className="text-[10px] text-[var(--color-text-muted)]">Session</span><p className="text-xs font-mono">{cd.sessionType}</p></div>}
          {cd.chartType && <div><span className="text-[10px] text-[var(--color-text-muted)]">Chart Type</span><p className="text-xs font-mono">{cd.chartType}</p></div>}
        </div>
      </GlassCard>

      {/* STEP 2: Market Structure */}
      <GlassCard className="p-4">
        <div className="flex items-center gap-2 mb-3">
          <BarChart3 className="w-4 h-4 text-cyber-400" />
          <h3 className="text-sm font-semibold">Market Structure</h3>
          <Tag color={
            ms.classification === 'bullish_trend' ? 'green' :
            ms.classification === 'bearish_trend' ? 'red' : 'amber'
          }>{ms.classification}</Tag>
        </div>
        <div className="flex flex-wrap gap-1.5 mb-2">
          <Tag color={ms.higherHighs ? 'green' : 'amber'}>HH:{ms.higherHighs ? 'YES' : 'NO'}</Tag>
          <Tag color={ms.higherLows ? 'green' : 'amber'}>HL:{ms.higherLows ? 'YES' : 'NO'}</Tag>
          <Tag color={ms.lowerHighs ? 'red' : 'amber'}>LH:{ms.lowerHighs ? 'YES' : 'NO'}</Tag>
          <Tag color={ms.lowerLows ? 'red' : 'amber'}>LL:{ms.lowerLows ? 'YES' : 'NO'}</Tag>
        </div>
        {ms.swingHighs && <div className="text-[11px] text-[var(--color-text-muted)]"><span className="text-[10px] font-medium">Swing Highs: </span>{ms.swingHighs}</div>}
        {ms.swingLows && <div className="text-[11px] text-[var(--color-text-muted)]"><span className="text-[10px] font-medium">Swing Lows: </span>{ms.swingLows}</div>}
      </GlassCard>

      {/* STEP 3: Liquidity */}
      <GlassCard className="p-4">
        <div className="flex items-center gap-2 mb-3">
          <Activity className="w-4 h-4 text-cyber-400" />
          <h3 className="text-sm font-semibold">Liquidity Analysis</h3>
          {liq.swept && <Tag color={liq.sweepType === 'bullish' ? 'green' : 'red'}>{liq.sweepType.toUpperCase()} SWEPT</Tag>}
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-1.5 text-[11px] text-[var(--color-text-muted)]">
          {liq.buySideLiquidity && <div><span className="text-[10px] font-medium">Buy-side: </span>{liq.buySideLiquidity}</div>}
          {liq.sellSideLiquidity && <div><span className="text-[10px] font-medium">Sell-side: </span>{liq.sellSideLiquidity}</div>}
          {liq.stopClusters && <div className="sm:col-span-2"><span className="text-[10px] font-medium">Stop Clusters: </span>{liq.stopClusters}</div>}
          {liq.liquidityPools && <div className="sm:col-span-2"><span className="text-[10px] font-medium">Liquidity Pools: </span>{liq.liquidityPools}</div>}
        </div>
        {(liq.equalHighs || liq.equalLows) && (
          <div className="flex gap-1.5 mt-2">
            {liq.equalHighs && <Tag color="blue">Equal Highs</Tag>}
            {liq.equalLows && <Tag color="blue">Equal Lows</Tag>}
          </div>
        )}
      </GlassCard>

      {/* STEP 4: SMC */}
      {(smc.bos || smc.choch || smc.mss) && (
        <GlassCard className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <Activity className="w-4 h-4 text-cyber-400" />
            <h3 className="text-sm font-semibold">Smart Money Concepts</h3>
          </div>
          <div className="space-y-1.5 text-[11px] text-[var(--color-text-muted)]">
            {smc.bos && <div><span className="text-[10px] font-medium">BOS </span><Tag color={smc.bosConfidence >= 70 ? 'green' : 'amber'}>{smc.bosConfidence}%</Tag> {smc.bos}</div>}
            {smc.choch && <div><span className="text-[10px] font-medium">CHOCH </span><Tag color={smc.chochConfidence >= 70 ? 'green' : 'amber'}>{smc.chochConfidence}%</Tag> {smc.choch}</div>}
            {smc.mss && <div><span className="text-[10px] font-medium">MSS </span><Tag color={smc.mssConfidence >= 70 ? 'green' : 'amber'}>{smc.mssConfidence}%</Tag> {smc.mss}</div>}
          </div>
        </GlassCard>
      )}

      {/* STEP 5: FVGs */}
      {fvgs.length > 0 && (
        <GlassCard className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <Target className="w-4 h-4 text-cyber-400" />
            <h3 className="text-sm font-semibold">Fair Value Gaps</h3>
          </div>
          <div className="space-y-2">
            {fvgs.map((fvg, i) => (
              <div key={i} className="flex items-center justify-between text-[11px] text-[var(--color-text-muted)] bg-white/5 rounded p-2">
                <div className="flex items-center gap-2">
                  <Tag color={fvg.type === 'bullish' ? 'green' : 'red'}>{fvg.type.toUpperCase()}</Tag>
                  <span>{fvg.bottom} - {fvg.top} <span className="text-[10px]">(mid: {fvg.midpoint})</span></span>
                </div>
                <div className="flex items-center gap-2">
                  <Tag color={fvg.status === 'untouched' ? 'green' : fvg.status === 'partially_filled' ? 'amber' : 'red'}>{fvg.status}</Tag>
                  <span className="text-[10px] font-mono">S:{fvg.strength}</span>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      )}

      {/* STEP 6: Order Blocks */}
      {obs.length > 0 && (
        <GlassCard className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <Shield className="w-4 h-4 text-cyber-400" />
            <h3 className="text-sm font-semibold">Order Blocks</h3>
          </div>
          <div className="flex flex-wrap gap-2">
            {obs.map((ob, i) => (
              <div key={i} className="flex items-center gap-1.5 bg-white/5 rounded px-2 py-1 text-[11px] text-[var(--color-text-muted)]">
                <Tag color={ob.type === 'bullish' ? 'green' : 'red'}>{ob.type.toUpperCase()}</Tag>
                <span>{ob.zone}</span>
                <Tag color={ob.status === 'unmitigated' || ob.status === 'fresh' ? 'green' : 'amber'}>{ob.status}</Tag>
              </div>
            ))}
          </div>
        </GlassCard>
      )}

      {/* STEP 7: Premium/Discount */}
      {pd.dealingRange && (
        <GlassCard className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <Activity className="w-4 h-4 text-cyber-400" />
            <h3 className="text-sm font-semibold">Premium / Discount</h3>
            <Tag color={pd.currentPosition === 'discount' ? 'green' : pd.currentPosition === 'premium' ? 'red' : 'amber'}>{pd.currentPosition}</Tag>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-1 text-[11px] text-[var(--color-text-muted)]">
            {pd.dealingRange && <div><span className="text-[10px] font-medium">Range: </span>{pd.dealingRange}</div>}
            {pd.equilibrium && <div><span className="text-[10px] font-medium">EQ: </span>{pd.equilibrium}</div>}
            {pd.premiumZone && <div><span className="text-[10px] font-medium">Premium: </span>{pd.premiumZone}</div>}
            {pd.discountZone && <div><span className="text-[10px] font-medium">Discount: </span>{pd.discountZone}</div>}
          </div>
        </GlassCard>
      )}

      {/* STEP 8: Volume */}
      {(vol.spikes || vol.absorption || vol.exhaustion) && (
        <GlassCard className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <BarChart3 className="w-4 h-4 text-cyber-400" />
            <h3 className="text-sm font-semibold">Volume Analysis</h3>
          </div>
          <div className="space-y-1 text-[11px] text-[var(--color-text-muted)]">
            {vol.spikes && <div><span className="text-[10px] font-medium">Spikes: </span>{vol.spikes}</div>}
            {vol.absorption && <div><span className="text-[10px] font-medium">Absorption: </span>{vol.absorption}</div>}
            {vol.exhaustion && <div><span className="text-[10px] font-medium">Exhaustion: </span>{vol.exhaustion}</div>}
            {vol.breakoutVolume && <div><span className="text-[10px] font-medium">Breakout Vol: </span>{vol.breakoutVolume}</div>}
          </div>
        </GlassCard>
      )}

      {/* STEP 9: Momentum */}
      {(mom.impulsive || mom.corrective || mom.consolidation) && (
        <GlassCard className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <Zap className="w-4 h-4 text-cyber-400" />
            <h3 className="text-sm font-semibold">Momentum Analysis</h3>
            <Tag color={mom.score >= 70 ? 'green' : mom.score >= 40 ? 'amber' : 'red'}>{mom.score}/100</Tag>
          </div>
          <div className="space-y-1 text-[11px] text-[var(--color-text-muted)]">
            {mom.impulsive && <div><span className="text-[10px] font-medium">Impulsive: </span>{mom.impulsive}</div>}
            {mom.corrective && <div><span className="text-[10px] font-medium">Corrective: </span>{mom.corrective}</div>}
            {mom.consolidation && <div><span className="text-[10px] font-medium">Consolidation: </span>{mom.consolidation}</div>}
            {mom.compression && <div><span className="text-[10px] font-medium">Compression: </span>{mom.compression}</div>}
          </div>
        </GlassCard>
      )}

      {/* Signal Validation Engine */}
      {validation && (
        <ValidationReportCard report={validation} />
      )}

      {/* Scoring Breakdown */}
      {scoring.total > 0 && (
        <GlassCard className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <Activity className="w-4 h-4 text-cyber-400" />
            <h3 className="text-sm font-semibold">Confidence Breakdown</h3>
            <span className="text-sm font-bold font-mono text-aurora-400">{scoring.total}/100</span>
          </div>
          <ScoringBars scoring={scoring} />
        </GlassCard>
      )}

      {/* Trade Plan */}
      {trade.bias !== 'NO_TRADE' && trade.entry && (
        <GlassCard className="p-5">
          <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/5">
            <Target className="w-4 h-4 text-aurora-400" />
            <h3 className="text-sm font-semibold">Trade Plan</h3>
            {trade.riskReward && <Tag color="green">RR {trade.riskReward}</Tag>}
            {trade.probabilityScore && <Tag color="blue">P: {trade.probabilityScore}%</Tag>}
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3">
            <div className="min-w-0"><span className="text-xs text-[var(--color-text-muted)]">Entry</span><p className="font-mono text-sm font-medium break-all">{trade.entry}</p></div>
            <div className="min-w-0"><span className="text-xs text-[var(--color-text-muted)]">Stop Loss</span><p className="font-mono text-sm font-medium text-red-400 break-all">{trade.stop}</p></div>
            {trade.tp1 && <div className="min-w-0"><span className="text-xs text-[var(--color-text-muted)]">TP1</span><p className="font-mono text-sm font-medium text-aurora-400 break-all">{trade.tp1}</p></div>}
            {trade.tp2 && <div className="min-w-0"><span className="text-xs text-[var(--color-text-muted)]">TP2</span><p className="font-mono text-sm font-medium text-aurora-400 break-all">{trade.tp2}</p></div>}
            {trade.tp3 && <div className="min-w-0"><span className="text-xs text-[var(--color-text-muted)]">TP3</span><p className="font-mono text-sm font-medium text-aurora-400 break-all">{trade.tp3}</p></div>}
          </div>
        </GlassCard>
      )}
        </>
      )}
    </motion.div>
  );
});
