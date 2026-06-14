// ---- Core Market Types ----

export type ExchangeName = 'binance' | 'bybit' | 'hyperliquid';

export type Timeframe = '1m' | '3m' | '5m' | '15m' | '30m' | '1h' | '4h';

export const SUPPORTED_SYMBOLS = [
  'BTCUSDT',
  'ETHUSDT',
  'SOLUSDT',
  'BNBUSDT',
  'XRPUSDT',
] as const;

export type SupportedSymbol = typeof SUPPORTED_SYMBOLS[number];

export const SUPPORTED_TIMEFRAMES: Timeframe[] = [
  '1m', '3m', '5m', '15m', '30m', '1h', '4h',
];

export const TIMEFRAME_LABELS: Record<Timeframe, string> = {
  '1m': '1m',
  '3m': '3m',
  '5m': '5m',
  '15m': '15m',
  '30m': '30m',
  '1h': '1h',
  '4h': '4h',
};

export const TIMEFRAME_MS: Record<Timeframe, number> = {
  '1m': 60_000,
  '3m': 180_000,
  '5m': 300_000,
  '15m': 900_000,
  '30m': 1_800_000,
  '1h': 3_600_000,
  '4h': 14_400_000,
};

// ---- Data Models ----

export interface Candle {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  exchange?: string;
  symbol?: string;
  timeframe?: string;
}

export interface Ticker {
  symbol: string;
  price: number;
  change_24h: number;
  volume_24h: number;
  high_24h: number;
  low_24h: number;
  exchange: string;
  timestamp: number;
}

export interface OrderBookLevel {
  price: number;
  volume: number;
}

export interface OrderBook {
  symbol: string;
  exchange: string;
  bids: OrderBookLevel[];
  asks: OrderBookLevel[];
  spread: number;
  mid_price: number;
  timestamp: number;
}

export interface MarketDataResponse {
  symbol: string;
  timeframe: string;
  exchange: string;
  candles: Candle[];
  timestamp: number;
}

export interface ExchangeStatus {
  exchange: string;
  connected: boolean;
  symbols: string[];
  latency_ms: number | null;
  last_update: number | null;
  error: string | null;
}

export interface WSMessage {
  type: 'candle' | 'ticker' | 'orderbook' | 'status' | 'connected' | 'error' | 'pong' | 'subscribed' | 'candles_data';
  exchange: string;
  symbol: string;
  timeframe?: string;
  data?: unknown;
  candles?: Candle[];
  message?: string;
  timestamp: number;
}

// ---- Hook State Types ----

export interface MarketDataState {
  candles: Record<string, Candle[]>;       // key: `${symbol}:${timeframe}`
  tickers: Record<string, Ticker>;         // key: symbol
  orderBooks: Record<string, OrderBook>;   // key: symbol
  exchangeStatuses: ExchangeStatus[];
  isConnected: boolean;
  selectedExchange: ExchangeName;
  selectedSymbol: SupportedSymbol;
  selectedTimeframe: Timeframe;
  lastUpdate: number | null;
  error: string | null;
}

export interface MarketDataActions {
  setSelectedExchange: (exchange: ExchangeName) => void;
  setSelectedSymbol: (symbol: SupportedSymbol) => void;
  setSelectedTimeframe: (timeframe: Timeframe) => void;
  connect: () => void;
  disconnect: () => void;
  fetchCandles: (symbol: string, timeframe: string, exchange?: string) => Promise<Candle[]>;
  fetchTicker: (symbol: string, exchange?: string) => Promise<Ticker | null>;
  fetchOrderBook: (symbol: string, exchange?: string) => Promise<OrderBook | null>;
}

// ---- API Types ----

export interface CandlesQueryParams {
  symbol: string;
  timeframe?: Timeframe;
  exchange?: ExchangeName;
  limit?: number;
}

export interface MultiTimeframeParams {
  symbol: string;
  timeframes: Timeframe[];
  exchange?: ExchangeName;
}

// ---- WebSocket Types ----

export interface WSSubscriptionMessage {
  type: 'subscribe' | 'unsubscribe';
  symbol: string;
  timeframe?: string;
}

export interface WSFetchCandlesMessage {
  type: 'fetch_candles';
  symbol: string;
  timeframe?: string;
  limit?: number;
}
