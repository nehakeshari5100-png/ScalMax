'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import type {
  IndicatorSet,
  IndicatorResponse,
  IndicatorState,
} from '@/types/indicators';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface UseIndicatorsOptions {
  symbol?: string;
  timeframe?: string;
  exchange?: string;
  autoFetch?: boolean;
  pollInterval?: number;
}

const INITIAL_STATE: IndicatorState = {
  data: null,
  loading: false,
  error: null,
  lastUpdate: null,
};

export function useIndicators(options: UseIndicatorsOptions = {}) {
  const {
    symbol = 'BTCUSDT',
    timeframe = '5m',
    exchange = 'binance',
    autoFetch = true,
    pollInterval = 0,
  } = options;

  const [state, setState] = useState<IndicatorState>(INITIAL_STATE);
  const pollTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const isMountedRef = useRef(true);

  const fetchIndicators = useCallback(async (
    sym?: string,
    tf?: string,
    ex?: string,
  ): Promise<IndicatorSet | null> => {
    const symbolToUse = sym || symbol;
    const tfToUse = tf || timeframe;
    const exToUse = ex || exchange;

    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const params = new URLSearchParams({
        timeframe: tfToUse,
        exchange: exToUse,
        lookback: '500',
      });

      const response = await fetch(
        `${API_BASE}/api/indicators/${symbolToUse}?${params}`
      );

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      const result: IndicatorResponse = await response.json();

      if (result.success && result.data) {
        setState({
          data: result.data,
          loading: false,
          error: null,
          lastUpdate: Date.now(),
        });
        return result.data;
      } else {
        throw new Error(result.error || 'Indicator calculation failed');
      }
    } catch (e) {
      const errorMsg = e instanceof Error ? e.message : 'Unknown error';
      setState(prev => ({ ...prev, loading: false, error: errorMsg }));
      return null;
    }
  }, [symbol, timeframe, exchange]);

  // ---- Polling ----
  useEffect(() => {
    if (!autoFetch) return;

    fetchIndicators();

    if (pollInterval > 0) {
      pollTimerRef.current = setInterval(() => {
        if (isMountedRef.current) {
          fetchIndicators();
        }
      }, pollInterval);
    }

    return () => {
      if (pollTimerRef.current) {
        clearInterval(pollTimerRef.current);
      }
    };
  }, [autoFetch, pollInterval, fetchIndicators]);

  useEffect(() => {
    isMountedRef.current = true;
    return () => { isMountedRef.current = false; };
  }, []);

  return {
    ...state,
    fetchIndicators,
    refetch: () => fetchIndicators(),
  };
}

// ---- Specialized Hooks ----

export function useTrendIndicators(symbol?: string, timeframe?: string) {
  const { data, loading, error } = useIndicators({ symbol, timeframe, autoFetch: true });
  return {
    ema9: data?.ema9 ?? 0,
    ema20: data?.ema20 ?? 0,
    ema50: data?.ema50 ?? 0,
    ema200: data?.ema200 ?? 0,
    trendScore: data?.trend_score ?? 0,
    loading,
    error,
  };
}

export function useMomentumIndicators(symbol?: string, timeframe?: string) {
  const { data, loading, error } = useIndicators({ symbol, timeframe, autoFetch: true });
  return {
    rsi: data?.rsi ?? 0,
    macd: data?.macd ?? { macd_line: 0, signal_line: 0, histogram: 0 },
    stochRsi: data?.stoch_rsi ?? { k: 0, d: 0, oversold: false, overbought: false },
    momentumScore: data?.momentum_score ?? 0,
    loading,
    error,
  };
}

export function useVolumeIndicators(symbol?: string, timeframe?: string) {
  const { data, loading, error } = useIndicators({ symbol, timeframe, autoFetch: true });
  return {
    vwap: data?.vwap ?? 0,
    volumeDelta: data?.volume_delta ?? 0,
    volumeSpike: data?.volume_spike ?? { is_spike: false, ratio: 0, direction: 'neutral' },
    loading,
    error,
  };
}

export function useVolatilityIndicators(symbol?: string, timeframe?: string) {
  const { data, loading, error } = useIndicators({ symbol, timeframe, autoFetch: true });
  return {
    atr: data?.atr ?? 0,
    atrPercent: data?.atr_percent ?? 0,
    bollinger: data?.bollinger ?? { upper: 0, middle: 0, lower: 0, bandwidth: 0, percent_b: 0 },
    volatilityScore: data?.volatility_score ?? 0,
    loading,
    error,
  };
}

export function useCompositeScores(symbol?: string, timeframe?: string) {
  const { data, loading, error } = useIndicators({ symbol, timeframe, autoFetch: true });
  return {
    trendScore: data?.trend_score ?? 0,
    momentumScore: data?.momentum_score ?? 0,
    volatilityScore: data?.volatility_score ?? 0,
    loading,
    error,
  };
}
