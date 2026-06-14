'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import type {
  Candle,
  Ticker,
  OrderBook,
  ExchangeStatus,
  ExchangeName,
  SupportedSymbol,
  Timeframe,
  MarketDataState,
  MarketDataActions,
  WSMessage,
} from '@/types/market';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const INITIAL_STATE: MarketDataState = {
  candles: {},
  tickers: {},
  orderBooks: {},
  exchangeStatuses: [],
  isConnected: false,
  selectedExchange: 'binance',
  selectedSymbol: 'BTCUSDT',
  selectedTimeframe: '5m',
  lastUpdate: null,
  error: null,
};

interface UseMarketDataOptions {
  autoConnect?: boolean;
  exchange?: ExchangeName;
  symbol?: SupportedSymbol;
  timeframe?: Timeframe;
}

export function useMarketData(options: UseMarketDataOptions = {}): MarketDataState & MarketDataActions {
  const [state, setState] = useState<MarketDataState>({
    ...INITIAL_STATE,
    selectedExchange: options.exchange || 'binance',
    selectedSymbol: options.symbol || 'BTCUSDT',
    selectedTimeframe: options.timeframe || '5m',
  });

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttemptRef = useRef(0);
  const maxReconnectDelay = 30_000;
  const isMountedRef = useRef(true);

  // ---- WebSocket Connection ----

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const wsUrl = `${API_BASE.replace(/^http/, 'ws')}/api/market/ws/${state.selectedExchange}`;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!isMountedRef.current) return;
        reconnectAttemptRef.current = 0;
        setState(prev => ({ ...prev, isConnected: true, error: null }));
      };

      ws.onmessage = (event) => {
        if (!isMountedRef.current) return;

        try {
          const msg: WSMessage = JSON.parse(event.data);

          switch (msg.type) {
            case 'candle': {
              if (msg.symbol && msg.timeframe && msg.data) {
                const candle = msg.data as Candle;
                const key = `${msg.symbol}:${msg.timeframe}`;
                setState(prev => {
                  const candles = { ...prev.candles };
                  const existing = [...(candles[key] || [])];

                  // Update last candle or append
                  if (existing.length > 0 && existing[existing.length - 1].timestamp === candle.timestamp) {
                    existing[existing.length - 1] = candle;
                  } else {
                    existing.push(candle);
                    if (existing.length > 500) existing.shift();
                  }

                  candles[key] = existing;
                  return { ...prev, candles, lastUpdate: Date.now() };
                });
              }
              break;
            }

            case 'ticker': {
              if (msg.symbol && msg.data) {
                const ticker = msg.data as Ticker;
                setState(prev => ({
                  ...prev,
                  tickers: { ...prev.tickers, [msg.symbol!]: ticker },
                  lastUpdate: Date.now(),
                }));
              }
              break;
            }

            case 'connected': {
              setState(prev => ({ ...prev, isConnected: true }));
              break;
            }

            case 'error': {
              setState(prev => ({ ...prev, error: msg.message || 'WebSocket error' }));
              break;
            }

            case 'pong':
              break;

            case 'candles_data': {
              if (msg.symbol && msg.timeframe && msg.candles) {
                const key = `${msg.symbol}:${msg.timeframe}`;
                setState(prev => ({
                  ...prev,
                  candles: { ...prev.candles, [key]: msg.candles! },
                  lastUpdate: Date.now(),
                }));
              }
              break;
            }
          }
        } catch (e) {
          console.error('[useMarketData] Failed to parse WS message:', e);
        }
      };

      ws.onerror = (event) => {
        if (!isMountedRef.current) return;
        setState(prev => ({ ...prev, error: 'WebSocket connection error' }));
      };

      ws.onclose = () => {
        if (!isMountedRef.current) return;
        setState(prev => ({ ...prev, isConnected: false }));
        scheduleReconnect();
      };
    } catch (e) {
      setState(prev => ({ ...prev, error: 'Failed to create WebSocket connection' }));
    }
  }, [state.selectedExchange]);

  const scheduleReconnect = useCallback(() => {
    if (!isMountedRef.current) return;

    const delay = Math.min(
      1000 * Math.pow(2, reconnectAttemptRef.current),
      maxReconnectDelay
    );
    reconnectAttemptRef.current++;

    reconnectTimerRef.current = setTimeout(() => {
      if (isMountedRef.current) {
        connect();
      }
    }, delay);
  }, [connect]);

  const disconnect = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    reconnectAttemptRef.current = 0;

    if (wsRef.current) {
      wsRef.current.onclose = null; // prevent reconnect
      wsRef.current.close();
      wsRef.current = null;
    }

    setState(prev => ({ ...prev, isConnected: false }));
  }, []);

  // ---- REST API Calls ----

  const fetchCandles = useCallback(async (
    symbol: string,
    timeframe: string,
    exchange?: string,
  ): Promise<Candle[]> => {
    try {
      const params = new URLSearchParams({ timeframe, limit: '100' });
      if (exchange) params.set('exchange', exchange);

      const response = await fetch(
        `${API_BASE}/api/market/candles/${symbol}?${params}`
      );
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const data = await response.json();
      const key = `${symbol}:${timeframe}`;

      setState(prev => ({
        ...prev,
        candles: { ...prev.candles, [key]: data.candles || [] },
        lastUpdate: Date.now(),
      }));

      return data.candles || [];
    } catch (e) {
      console.error('[useMarketData] fetchCandles error:', e);
      return [];
    }
  }, []);

  const fetchTicker = useCallback(async (
    symbol: string,
    exchange?: string,
  ): Promise<Ticker | null> => {
    try {
      const params = exchange ? `?exchange=${exchange}` : '';
      const response = await fetch(`${API_BASE}/api/market/ticker/${symbol}${params}`);
      if (!response.ok) return null;

      const ticker: Ticker = await response.json();
      setState(prev => ({
        ...prev,
        tickers: { ...prev.tickers, [ticker.symbol]: ticker },
      }));
      return ticker;
    } catch (e) {
      console.error('[useMarketData] fetchTicker error:', e);
      return null;
    }
  }, []);

  const fetchOrderBook = useCallback(async (
    symbol: string,
    exchange?: string,
  ): Promise<OrderBook | null> => {
    try {
      const params = exchange ? `?exchange=${exchange}` : '';
      const response = await fetch(`${API_BASE}/api/market/orderbook/${symbol}${params}`);
      if (!response.ok) return null;

      const ob: OrderBook = await response.json();
      setState(prev => ({
        ...prev,
        orderBooks: { ...prev.orderBooks, [ob.symbol]: ob },
      }));
      return ob;
    } catch (e) {
      console.error('[useMarketData] fetchOrderBook error:', e);
      return null;
    }
  }, []);

  // ---- Setters ----

  const setSelectedExchange = useCallback((exchange: ExchangeName) => {
    setState(prev => ({ ...prev, selectedExchange: exchange }));
  }, []);

  const setSelectedSymbol = useCallback((symbol: SupportedSymbol) => {
    setState(prev => ({ ...prev, selectedSymbol: symbol }));
  }, []);

  const setSelectedTimeframe = useCallback((timeframe: Timeframe) => {
    setState(prev => ({ ...prev, selectedTimeframe: timeframe }));
  }, []);

  // ---- Lifecycle ----

  useEffect(() => {
    isMountedRef.current = true;
    if (options.autoConnect !== false) {
      connect();
    }
    return () => {
      isMountedRef.current = false;
      disconnect();
    };
  }, [options.autoConnect, connect, disconnect]);

  // Reconnect when exchange changes
  useEffect(() => {
    disconnect();
    if (options.autoConnect !== false) {
      const timer = setTimeout(() => connect(), 100);
      return () => clearTimeout(timer);
    }
  }, [state.selectedExchange, connect, disconnect, options.autoConnect]);

  return {
    ...state,
    setSelectedExchange,
    setSelectedSymbol,
    setSelectedTimeframe,
    connect,
    disconnect,
    fetchCandles,
    fetchTicker,
    fetchOrderBook,
  };
}

// ---- Utility Hooks ----

export function useCandles(symbol: string, timeframe: Timeframe, exchange?: ExchangeName) {
  const { candles, fetchCandles, isConnected } = useMarketData({ autoConnect: false });
  const key = `${symbol}:${timeframe}`;

  useEffect(() => {
    if (isConnected) {
      // Data comes via WebSocket
    } else {
      fetchCandles(symbol, timeframe, exchange);
    }
  }, [symbol, timeframe, exchange, isConnected, fetchCandles]);

  return candles[key] || [];
}

export function useTicker(symbol: string) {
  const { tickers, fetchTicker, isConnected } = useMarketData({ autoConnect: false });

  useEffect(() => {
    if (!isConnected) {
      fetchTicker(symbol);
    }
  }, [symbol, isConnected, fetchTicker]);

  return tickers[symbol] || null;
}

export function useOrderBook(symbol: string) {
  const { orderBooks, fetchOrderBook, isConnected } = useMarketData({ autoConnect: false });

  useEffect(() => {
    if (!isConnected) {
      fetchOrderBook(symbol);
    }
  }, [symbol, isConnected, fetchOrderBook]);

  return orderBooks[symbol] || null;
}

export function useExchangeStatus() {
  const [statuses, setStatuses] = useState<ExchangeStatus[]>([]);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/market/status`);
        if (response.ok) {
          const data: ExchangeStatus[] = await response.json();
          setStatuses(data);
        }
      } catch {}
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 10_000);
    return () => clearInterval(interval);
  }, []);

  return statuses;
}
