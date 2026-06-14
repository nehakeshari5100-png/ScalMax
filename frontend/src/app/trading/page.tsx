'use client';

import { useState, useEffect, useCallback } from 'react';
import { cn, formatPrice, formatPercent } from '@/lib/utils';
import { PageContainer } from '@/components/layout/PageContainer';
import { GlassCard } from '@/components/ui/GlassCard';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { TradingViewChart } from '@/components/widgets/TradingViewChart';
import { AIAnalysisPanel } from '@/components/widgets/AIAnalysisPanel';
import { RiskCalculator } from '@/components/widgets/RiskCalculator';
import { api } from '@/lib/api';
import { ArrowUp, ArrowDown, TrendingUp, TrendingDown, Zap, Layers, Settings, Activity, Loader2, XCircle, BookOpen } from 'lucide-react';
import type { Position } from '@/types/papertrading';

export default function TradingPage() {
  const [symbol] = useState('BTCUSDT');
  const [accountId, setAccountId] = useState<string | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [ticker, setTicker] = useState<{ price: number; change24h: number; high24h: number; low24h: number; volume24h: number } | null>(null);
  const [analysis, setAnalysis] = useState<import('@/types/decision').DecisionOutput | null>(null);
  const [orderSide, setOrderSide] = useState<'long' | 'short'>('long');
  const [orderType, setOrderType] = useState('market');
  const [entryPrice, setEntryPrice] = useState('');
  const [quantity, setQuantity] = useState('0.001');
  const [stopLoss, setStopLoss] = useState('');
  const [takeProfit1, setTakeProfit1] = useState('');
  const [takeProfit2, setTakeProfit2] = useState('');
  const [showRiskCalc, setShowRiskCalc] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [activeTab, setActiveTab] = useState('Chart');
  const [timeframe, setTimeframe] = useState('5m');

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
    setLoading(true);
    setError(null);
    try {
      const aid = await loadAccount();
      setAccountId(aid);

      const [tokens, posRes] = await Promise.all([
        api.getTokens().catch(() => [] as import('@/types').Token[]),
        aid ? api.listPaperPositions({ account_id: aid, status: 'open' }) : Promise.resolve(null),
      ]);

      const tok = tokens.find((t) => t.symbol === symbol);
      if (tok) setTicker(tok);
      if (posRes?.success) setPositions(posRes.data);

      const pipeRes = await api.quickAnalysis({ symbol, timeframe, lookback: 200 });
      if (pipeRes.success && pipeRes.decision) setAnalysis(pipeRes.decision);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load trading data');
    } finally {
      setLoading(false);
    }
  }, [symbol, timeframe, loadAccount]);

  useEffect(() => { loadAll(); }, [loadAll]);

  const handleOpenPosition = async () => {
    if (!accountId) return;
    setSubmitting(true);
    try {
      const price = entryPrice ? parseFloat(entryPrice) : (ticker?.price || 0);
      const qty = parseFloat(quantity);
      const sl = stopLoss ? parseFloat(stopLoss) : price * 0.985;
      const tp1 = takeProfit1 ? parseFloat(takeProfit1) : price * 1.03;
      const tp2 = takeProfit2 ? parseFloat(takeProfit2) : undefined;

      const res = await api.openPaperPosition({
        account_id: accountId,
        symbol,
        direction: orderSide,
        entry_price: price,
        quantity: qty,
        stop_loss: sl,
        take_profit_1: tp1,
        take_profit_2: tp2 || null,
      });
      if (res.success) {
        setEntryPrice('');
        setStopLoss('');
        setTakeProfit1('');
        setTakeProfit2('');
        const posRes = await api.listPaperPositions({ account_id: accountId, status: 'open' });
        if (posRes.success) setPositions(posRes.data);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to open position');
    } finally {
      setSubmitting(false);
    }
  };

  const handleClosePosition = async (pos: Position) => {
    try {
      const price = ticker?.price || pos.entry_price;
      await api.closePaperPosition(pos.id, { position_id: pos.id, close_price: price, exit_reason: 'manual' });
      const posRes = await api.listPaperPositions({ account_id: accountId!, status: 'open' });
      if (posRes.success) setPositions(posRes.data);
    } catch {}
  };

  if (loading) return (
    <PageContainer>
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 text-aurora-400 animate-spin" />
      </div>
    </PageContainer>
  );

  return (
    <PageContainer>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-bold">{symbol.replace('USDT', '/USDT')}</h2>
              <span className="text-xl font-mono font-bold">{ticker ? formatPrice(ticker.price) : '-'}</span>
              {ticker && (
                <span className={cn('text-sm font-medium flex items-center gap-1', ticker.change24h >= 0 ? 'text-aurora-400' : 'text-red-400')}>
                  {ticker.change24h >= 0 ? <ArrowUp className="w-3.5 h-3.5" /> : <ArrowDown className="w-3.5 h-3.5" />}
                  {formatPercent(ticker.change24h)}
                </span>
              )}
            </div>
            {ticker && (
              <div className="flex items-center gap-3 text-xs text-[var(--color-text-muted)] mt-0.5">
                <span>Vol: ${(ticker.volume24h / 1e6).toFixed(1)}M</span>
                <span>H: ${formatPrice(ticker.high24h)}</span>
                <span>L: ${formatPrice(ticker.low24h)}</span>
              </div>
            )}
          </div>
          <div className="flex items-center gap-2 pl-4 border-l border-white/5">
            {['1m', '3m', '5m', '15m', '30m', '1h', '4h'].map(tf => (
              <button key={tf} onClick={() => setTimeframe(tf)}
                className={cn('px-2.5 py-1.5 text-xs font-medium rounded transition-all',
                  tf === timeframe ? 'bg-aurora-500/15 text-aurora-400 border border-aurora-500/20' : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'
                )}>
                {tf}
              </button>
            ))}
          </div>
        </div>
        <Button variant="outline" size="sm" onClick={loadAll}>
          <Loader2 className="w-3 h-3 mr-1" /> Refresh
        </Button>
      </div>

      {error && (
        <div className="flex items-center gap-2 px-4 py-2 mb-4 rounded-lg bg-red-500/10 border border-red-500/20 text-xs text-red-400">
          <XCircle className="w-3 h-3" /> {error}
        </div>
      )}

      <div className="grid xl:grid-cols-4 gap-5">
        <div className="xl:col-span-3 space-y-4">
          <div className="flex items-center gap-1 border-b border-white/5">
            {['Chart', 'Book', 'AI'].map(tab => (
              <button key={tab} onClick={() => setActiveTab(tab)}
                className={cn('px-4 py-2.5 text-xs font-medium transition-colors border-b-2 -mb-[1px]',
                  activeTab === tab ? 'text-aurora-400 border-aurora-400' : 'text-[var(--color-text-muted)] border-transparent hover:text-[var(--color-text)]'
                )}>
                {tab}
              </button>
            ))}
          </div>

          {activeTab === 'Chart' && (
            <TradingViewChart symbol={symbol} height={500} />
          )}

          {activeTab === 'Book' && (
            <GlassCard className="p-4">
              <p className="text-xs text-[var(--color-text-muted)]">Order book depth chart available with live data connection</p>
            </GlassCard>
          )}

          {activeTab === 'AI' && analysis && (
            <AIAnalysisPanel
              analysis={{
                direction: analysis.direction,
                confidence: analysis.confidence,
                reasoning: analysis.reasoning,
                levels: analysis.levels,
              }}
              symbol={symbol}
            />
          )}

          {positions.length > 0 && (
            <GlassCard className="p-0 overflow-hidden">
              <div className="flex items-center justify-between px-4 py-3 border-b border-white/5">
                <span className="text-xs font-semibold flex items-center gap-1.5">
                  <BookOpen className="w-3.5 h-3.5 text-aurora-400" /> Open Positions
                </span>
                <Badge variant="info" size="sm">{positions.length}</Badge>
              </div>
              <div className="divide-y divide-white/5">
                {positions.map(pos => (
                  <div key={pos.id} className="px-4 py-3 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Badge variant={pos.direction === 'long' ? 'long' : 'short'} size="sm">{pos.direction.toUpperCase()}</Badge>
                      <div>
                        <span className="text-sm font-semibold">{pos.symbol.replace('USDT', '')}</span>
                        <span className="text-xs text-[var(--color-text-muted)] ml-2">@{formatPrice(pos.entry_price)}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className={cn('text-sm font-bold font-mono', (pos.pnl || 0) >= 0 ? 'text-aurora-400' : 'text-red-400')}>
                        {(pos.pnl || 0) >= 0 ? '+' : ''}${(pos.pnl || 0).toFixed(2)}
                      </span>
                      <Button variant="danger" size="sm" onClick={() => handleClosePosition(pos)}>Close</Button>
                    </div>
                  </div>
                ))}
              </div>
            </GlassCard>
          )}
        </div>

        <div className="space-y-4">
          <GlassCard className="p-0 overflow-hidden">
            <div className="flex border-b border-white/5">
              <button onClick={() => setOrderSide('long')}
                className={cn('flex-1 py-3 text-sm font-semibold text-center transition-all',
                  orderSide === 'long' ? 'bg-green-500/15 text-green-400' : 'text-[var(--color-text-muted)]'
                )}>
                Long
              </button>
              <button onClick={() => setOrderSide('short')}
                className={cn('flex-1 py-3 text-sm font-semibold text-center transition-all',
                  orderSide === 'short' ? 'bg-red-500/15 text-red-400' : 'text-[var(--color-text-muted)]'
                )}>
                Short
              </button>
            </div>
            <div className="p-4 space-y-3">
              <Input label="Entry Price" placeholder={ticker ? `$${ticker.price.toFixed(2)}` : 'Auto'} value={entryPrice} onChange={e => setEntryPrice(e.target.value)} />
              <Input label="Amount (BTC)" placeholder="0.001" value={quantity} onChange={e => setQuantity(e.target.value)} />
              <Input label="Stop Loss" placeholder="Optional" value={stopLoss} onChange={e => setStopLoss(e.target.value)} />
              <Input label="Take Profit 1" placeholder="Optional" value={takeProfit1} onChange={e => setTakeProfit1(e.target.value)} />
              <Input label="Take Profit 2" placeholder="Optional" value={takeProfit2} onChange={e => setTakeProfit2(e.target.value)} />

              <Button
                variant={orderSide === 'long' ? 'primary' : 'danger'}
                className="w-full"
                onClick={handleOpenPosition}
                loading={submitting}
                icon={orderSide === 'long' ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
              >
                {orderSide === 'long' ? 'Open Long' : 'Open Short'}
              </Button>
            </div>
          </GlassCard>

          <button onClick={() => setShowRiskCalc(!showRiskCalc)} className="w-full text-left">
            <GlassCard className="py-2">
              <div className="flex items-center justify-between text-sm">
                <span className="flex items-center gap-2 text-cyber-400"><Settings className="w-4 h-4" /> Risk Calculator</span>
                <span className="text-[var(--color-text-muted)]">{showRiskCalc ? '▲' : '▼'}</span>
              </div>
            </GlassCard>
          </button>
          {showRiskCalc && <RiskCalculator entry={ticker?.price || 0} stopLoss={0} />}
        </div>
      </div>
    </PageContainer>
  );
}
