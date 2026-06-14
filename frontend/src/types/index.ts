export type Direction = 'long' | 'short' | 'neutral';
export type Timeframe = '1m' | '3m' | '5m' | '15m' | '30m' | '1h' | '4h';
export type SignalStatus = 'active' | 'filled' | 'expired' | 'cancelled';
export type OrderSide = 'buy' | 'sell';
export type ExecutionMode = 'manual' | 'auto';

export interface Token {
  symbol: string;
  baseAsset: string;
  quoteAsset: string;
  price: number;
  change24h: number;
  volume24h: number;
  high24h: number;
  low24h: number;
  marketCap?: number;
}

export interface IndicatorValues {
  rsi: number;
  macd: { value: number; signal: number; histogram: number };
  ema: Record<number, number>;
  sma: Record<number, number>;
  bb: { upper: number; middle: number; lower: number };
  atr: number;
  obv: number;
  vwap: number;
}

export interface MarketStructure {
  swingHighs: { price: number; timestamp: number }[];
  swingLows: { price: number; timestamp: number }[];
  orderBlocks: OrderBlock[];
  fairValueGaps: FVG[];
  liquidityZones: LiquidityZone[];
  marketPhase: 'trending_up' | 'trending_down' | 'ranging' | 'volatile';
  currentBias: Direction;
}

export interface OrderBlock {
  type: 'bullish' | 'bearish';
  startPrice: number;
  endPrice: number;
  startTime: number;
  endTime: number;
  strength: number;
  mitigated: boolean;
}

export interface FVG {
  direction: 'bullish' | 'bearish';
  gapHigh: number;
  gapLow: number;
  gapSize: number;
  startTime: number;
  mitigated: boolean;
  strength: number;
}

export interface LiquidityZone {
  type: 'support' | 'resistance';
  price: number;
  strength: number;
  touches: number;
}

export interface ConfluenceScore {
  overall: number;
  direction: Direction;
  components: {
    indicator: { score: number; weight: number };
    structure: { score: number; weight: number };
    liquidity: { score: number; weight: number };
    ai: { score: number; weight: number };
  };
  conflicts: string[];
}

export interface Signal {
  id: string;
  symbol: string;
  direction: Direction;
  entry: number;
  stopLoss: number;
  takeProfit: number[];
  confidence: number;
  timeframe: Timeframe;
  timestamp: number;
  status: SignalStatus;
  confluenceScore: ConfluenceScore;
  aiAnalysis?: AIAnalysis;
  strategy: string;
  executionMode: ExecutionMode;
  metadata: Record<string, unknown>;
}

export interface AIAnalysis {
  model: string;
  direction: Direction;
  confidence: number;
  analysis: string;
  keyLevels: { support: number[]; resistance: number[] };
  riskNotes: string[];
  timestamp: number;
  rawResponse?: string;
}

export interface Trade {
  id: string;
  signalId: string;
  symbol: string;
  side: OrderSide;
  entryPrice: number;
  exitPrice: number | null;
  quantity: number;
  leverage: number;
  pnl: number | null;
  pnlPercent: number | null;
  fees: number;
  entryTime: number;
  exitTime: number | null;
  stopLoss: number;
  takeProfit: number[];
  status: 'open' | 'closed' | 'stopped' | 'cancelled';
  tags: string[];
  notes: string;
  screenshot?: string;
}

export interface PortfolioStats {
  totalEquity: number;
  availableBalance: number;
  openPnl: number;
  dailyPnl: number;
  weeklyPnl: number;
  monthlyPnl: number;
  winRate: number;
  profitFactor: number;
  sharpeRatio: number;
  maxDrawdown: number;
  totalTrades: number;
  avgTradeDuration: number;
  bestTrade: number;
  worstTrade: number;
}

export interface ScannerResult {
  symbol: string;
  price: number;
  change24h: number;
  volume24h: number;
  signal: Direction;
  confidence: number;
  score: number;
  patterns: string[];
  timeframes: Timeframe[];
}

export interface RiskParameters {
  maxPositionSize: number;
  maxLeverage: number;
  defaultStopLoss: number;
  defaultTakeProfit: number[];
  dailyLossLimit: number;
  maxOpenPositions: number;
  riskPerTrade: number;
  positionSizing: 'fixed' | 'percentage' | 'kelly' | 'volatility';
  executionMode: ExecutionMode;
}

export interface UserSettings {
  openRouterApiKey: string;
  openRouterModel: string;
  exchanges: { name: string; enabled: boolean; apiKey?: string; secret?: string }[];
  riskParameters: RiskParameters;
  theme: 'dark' | 'light';
  notifications: boolean;
  timeframe: Timeframe;
}

// ---- OpenRouter Types ----

export interface OpenRouterModel {
  id: string;
  name: string;
  created: number;
  description: string;
  context_length: number;
  architecture: { modality: string; tokenizer: string; instruct_type: string | null };
  pricing: { prompt: string; completion: string; image: string; request: string };
  top_provider: { max_completion_tokens: number | null; is_moderated: boolean };
  per_request_limits: { prompt_tokens: number | null; completion_tokens: number | null };
}

export interface OpenRouterChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface OpenRouterChatRequest {
  model: string;
  messages: OpenRouterChatMessage[];
  temperature?: number;
  top_p?: number;
  max_tokens?: number;
  stream?: boolean;
  frequency_penalty?: number;
  presence_penalty?: number;
}

export interface OpenRouterChatResponse {
  id: string;
  model: string;
  choices: {
    index: number;
    message: OpenRouterChatMessage;
    finish_reason: 'stop' | 'length' | 'error' | null;
  }[];
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

export interface OpenRouterStreamChunk {
  id: string;
  model: string;
  choices: {
    index: number;
    delta: { role?: string; content?: string };
    finish_reason: 'stop' | 'length' | null;
  }[];
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

export interface OpenRouterCostEntry {
  model: string;
  timestamp: number;
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
  promptCost: number;
  completionCost: number;
  totalCost: number;
  sessionId: string;
}

export interface OpenRouterSessionStats {
  totalCost: number;
  totalTokens: number;
  totalRequests: number;
  averageTokensPerRequest: number;
  modelBreakdown: Record<string, { requests: number; cost: number; tokens: number }>;
  costHistory: OpenRouterCostEntry[];
}

export interface ConnectionTestResult {
  success: boolean;
  latency: number;
  model: string;
  error?: string;
}
