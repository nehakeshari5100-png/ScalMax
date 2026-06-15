'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { cn } from '@/lib/utils';
import { api } from '@/lib/api';
import { Maximize2, Crosshair, Loader2 } from 'lucide-react';

interface ChartProps {
  symbol?: string;
  height?: number;
  className?: string;
  showControls?: boolean;
}

interface Candle {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export function TradingViewChart({ symbol = 'BTCUSDT', height = 400, className, showControls = true }: ChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [timeframe, setTimeframe] = useState('5m');
  const [loading, setLoading] = useState(true);
  const dataRef = useRef<Candle[]>([]);
  const mousePos = useRef({ x: 0, y: 0 });
  const [crosshairPrice, setCrosshairPrice] = useState<number | null>(null);
  const [crosshairTime, setCrosshairTime] = useState<string | null>(null);

  const timeframes = ['1m', '3m', '5m', '15m', '30m', '1h'];

  const fetchCandles = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.getCandles(symbol, timeframe, 200);
      if (Array.isArray(res)) {
        const candles: Candle[] = (res as Array<{ time?: number; timestamp?: number; open: number; high: number; low: number; close: number; volume: number }>).map((c) => ({
          time: c.time?.toString() || (c.timestamp ? new Date(c.timestamp * 1000).toISOString() : new Date().toISOString()),
          open: c.open,
          high: c.high,
          low: c.low,
          close: c.close,
          volume: c.volume,
        }));
        dataRef.current = candles;
      }
    } catch {
      // Generate sample candles as fallback
      const base = symbol === 'BTCUSDT' ? 67542 : symbol === 'ETHUSDT' ? 3456 : 150;
      dataRef.current = Array.from({ length: 150 }, (_, i) => {
        const t = Date.now() - (150 - i) * 300000;
        const o = base + Math.sin(i * 0.1) * 200 + (Math.random() - 0.5) * 50;
        const c = o + (Math.random() - 0.48) * 30;
        return {
          time: new Date(t).toISOString(),
          open: o,
          high: Math.max(o, c) + Math.random() * 20,
          low: Math.min(o, c) - Math.random() * 20,
          close: c,
          volume: Math.random() * 500 + 50,
        };
      });
    } finally {
      setLoading(false);
    }
  }, [symbol, timeframe]);

  useEffect(() => {
    fetchCandles();
  }, [fetchCandles]);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const rect = container.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    const w = rect.width;
    const h = height;

    canvas.width = w * dpr;
    canvas.height = h * dpr;
    canvas.style.width = `${w}px`;
    canvas.style.height = `${h}px`;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.scale(dpr, dpr);

    const data = dataRef.current;
    if (data.length === 0) return;

    const padding = { top: 30, right: 20, bottom: 35, left: 60 };
    const chartW = w - padding.left - padding.right;
    const chartH = h - padding.top - padding.bottom;

    const prices = data.map(d => d.high);
    const maxPrice = Math.max(...prices);
    const minPrice = Math.min(...data.map(d => d.low));
    const priceRange = maxPrice - minPrice || 1;
    const padR = priceRange * 0.08;
    const yMax = maxPrice + padR;
    const yMin = minPrice - padR;
    const yRange = yMax - yMin;
    const totalVol = Math.max(...data.map(d => d.volume));

    const toX = (i: number) => padding.left + (i / (data.length - 1)) * chartW;
    const toY = (price: number) => padding.top + chartH - ((price - yMin) / yRange) * chartH;

    ctx.strokeStyle = 'rgba(255,255,255,0.03)';
    ctx.lineWidth = 1;
    for (let i = 0; i < 8; i++) {
      const y = padding.top + (chartH / 8) * i;
      ctx.beginPath(); ctx.moveTo(padding.left, y); ctx.lineTo(w - padding.right, y); ctx.stroke();
      const pl = yMax - (yRange / 8) * i;
      ctx.fillStyle = '#64748b';
      ctx.font = '10px JetBrains Mono, monospace';
      ctx.textAlign = 'right';
      ctx.fillText((pl ?? 0).toFixed(2), padding.left - 8, y + 3);
    }

    for (let i = 0; i < 6; i++) {
      const x = padding.left + (chartW / 6) * i;
      ctx.beginPath(); ctx.moveTo(x, padding.top); ctx.lineTo(x, h - padding.bottom); ctx.stroke();
      const idx = Math.floor((data.length / 6) * i);
      if (data[idx]) {
        ctx.fillStyle = '#64748b';
        ctx.font = '10px JetBrains Mono, monospace';
        ctx.textAlign = 'center';
        const d = new Date(data[idx].time);
        ctx.fillText(`${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`, x, h - 12);
      }
    }

    const volWidth = Math.max(1, chartW / data.length * 0.6);
    data.forEach((d, i) => {
      const x = toX(i) - volWidth / 2;
      const volH = (d.volume / totalVol) * chartH * 0.2;
      ctx.fillStyle = d.close >= d.open ? 'rgba(0, 196, 140, 0.15)' : 'rgba(239, 68, 68, 0.15)';
      ctx.fillRect(x, h - padding.bottom - volH - 2, volWidth, volH);
    });

    const candleWidth = Math.max(2, chartW / data.length * 0.7);
    data.forEach((d, i) => {
      const x = toX(i);
      const isUp = d.close >= d.open;
      ctx.fillStyle = isUp ? '#00c48c' : '#ef4444';
      ctx.strokeStyle = isUp ? '#00c48c' : '#ef4444';
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(x, toY(d.high)); ctx.lineTo(x, toY(d.low)); ctx.stroke();
      const bodyTop = toY(Math.max(d.open, d.close));
      const bodyBottom = toY(Math.min(d.open, d.close));
      const bodyH = Math.max(1, bodyBottom - bodyTop);
      if (candleWidth >= 3) ctx.fillRect(x - candleWidth / 2, bodyTop, candleWidth, bodyH);
      else { ctx.beginPath(); ctx.moveTo(x, toY(d.open)); ctx.lineTo(x, toY(d.close)); ctx.stroke(); }
    });

    const emaPeriod = 9;
    for (let i = emaPeriod; i < data.length; i++) {
      const ema = data.slice(i - emaPeriod, i).reduce((s, d) => s + d.close, 0) / emaPeriod;
      const prevEma = data.slice(i - emaPeriod - 1, i - 1).reduce((s, d) => s + d.close, 0) / emaPeriod;
      ctx.strokeStyle = 'rgba(0, 196, 140, 0.5)';
      ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.moveTo(toX(i - 1), toY(prevEma)); ctx.lineTo(toX(i), toY(ema)); ctx.stroke();
    }

    if (crosshairPrice !== null) {
      ctx.strokeStyle = 'rgba(255,255,255,0.15)';
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 4]);
      ctx.beginPath(); ctx.moveTo(mousePos.current.x, padding.top); ctx.lineTo(mousePos.current.x, h - padding.bottom); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(padding.left, mousePos.current.y); ctx.lineTo(w - padding.right, mousePos.current.y); ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = 'rgba(30, 32, 53, 0.9)';
      ctx.strokeStyle = 'rgba(255,255,255,0.1)';
      const labelText = `${(crosshairPrice ?? 0).toFixed(2)}`;
      ctx.beginPath();
      ctx.roundRect(Math.min(mousePos.current.x, w - ctx.measureText(labelText).width - 24), 0, ctx.measureText(labelText).width + 16, 22, 4);
      ctx.fill(); ctx.stroke();
      ctx.fillStyle = '#f1f5f9';
      ctx.font = '11px JetBrains Mono, monospace';
      ctx.textAlign = 'center';
      ctx.fillText(labelText, Math.min(mousePos.current.x, w - ctx.measureText(labelText).width / 2 - 14), 15);
    }

    ctx.strokeStyle = 'rgba(255,255,255,0.05)';
    ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(padding.left, padding.top); ctx.lineTo(padding.left, h - padding.bottom); ctx.stroke();
  }, [height, crosshairPrice]);

  useEffect(() => {
    if (!loading) {
      setTimeout(() => draw(), 50);
    }
  }, [draw, loading]);

  useEffect(() => {
    const resizeObserver = new ResizeObserver(() => draw());
    if (containerRef.current) resizeObserver.observe(containerRef.current);
    return () => resizeObserver.disconnect();
  }, [draw]);

  const handleMouseMove = (e: React.MouseEvent) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    mousePos.current = { x, y };

    const data = dataRef.current;
    if (data.length === 0) return;

    const padding = { top: 30, right: 20, bottom: 35, left: 60 };
    const chartW = rect.width - padding.left - padding.right;
    const chartH = (height || 400) - padding.top - padding.bottom;
    const index = Math.round(((x - padding.left) / chartW) * (data.length - 1));

    if (index >= 0 && index < data.length) {
      const prices = data.map(d => d.high);
      const maxPrice = Math.max(...prices);
      const minPrice = Math.min(...data.map(d => d.low));
      const priceRange = maxPrice - minPrice || 1;
      const padding_range = priceRange * 0.08;
      const yMax = maxPrice + padding_range;
      const yMin = minPrice - padding_range;
      const yRange = yMax - yMin;
      const price = yMax - ((y - padding.top) / chartH) * yRange;
      setCrosshairPrice(price);
      setCrosshairTime(new Date(data[index].time).toLocaleTimeString());
    }
  };

  const handleMouseLeave = () => {
    setCrosshairPrice(null);
    setCrosshairTime(null);
  };

  return (
    <div ref={containerRef} className={cn('glass rounded-xl border border-white/5 relative', className)} style={{ height }}>
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center z-20 bg-[#0b0d19]/80">
          <Loader2 className="w-6 h-6 text-aurora-400 animate-spin" />
        </div>
      )}
      <div className="absolute top-0 left-0 right-0 z-10 flex items-center justify-between px-4 py-2">
        <div className="flex items-center gap-3">
          <span className="text-sm font-semibold">{symbol}</span>
          {crosshairPrice && crosshairTime && (
            <span className="text-xs font-mono text-[var(--color-text-muted)]">{crosshairTime} — ${(crosshairPrice ?? 0).toFixed(2)}</span>
          )}
        </div>
        {showControls && (
          <div className="flex items-center gap-1">
            {timeframes.map(tf => (
              <button key={tf} onClick={() => { setTimeframe(tf); }}
                className={cn('px-2 py-1 text-xs rounded transition-colors',
                  timeframe === tf ? 'bg-aurora-500/15 text-aurora-400' : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'
                )}>{tf}</button>
            ))}
            <div className="w-px h-4 bg-white/5 mx-1" />
            <button className="p-1 text-[var(--color-text-muted)] hover:text-[var(--color-text)]"><Crosshair className="w-3.5 h-3.5" /></button>
          </div>
        )}
      </div>
      <canvas ref={canvasRef} className="w-full cursor-crosshair" onMouseMove={handleMouseMove} onMouseLeave={handleMouseLeave} />
    </div>
  );
}
