// ---- Indicator Types ----

export interface EMAData {
  ema9: number;
  ema20: number;
  ema50: number;
  ema200: number;
}

export interface MACDData {
  macd_line: number;
  signal_line: number;
  histogram: number;
}

export interface RSIData {
  rsi: number;
  oversold: boolean;
  overbought: boolean;
}

export interface StochRSIData {
  k: number;
  d: number;
  oversold: boolean;
  overbought: boolean;
}

export interface VWAPData {
  vwap: number;
  price_above_vwap: boolean | null;
}

export interface ATRData {
  atr: number;
  atr_percent: number;
}

export interface BollingerBandsData {
  upper: number;
  middle: number;
  lower: number;
  bandwidth: number;
  percent_b: number;
}

export interface VolumeSpikeData {
  is_spike: boolean;
  ratio: number;
  direction: string;
}

export interface TrendStrengthData {
  score: number;
  direction: string;
  description: string;
}

export interface MomentumStrengthData {
  score: number;
  direction: string;
  description: string;
}

export interface VolatilityData {
  score: number;
  description: string;
}

export interface IndicatorSet {
  symbol: string;
  timeframe: string;
  timestamp: number;

  // Trend
  ema9: number;
  ema20: number;
  ema50: number;
  ema200: number;

  // Momentum
  rsi: number;
  macd: MACDData;
  stoch_rsi: StochRSIData;

  // Volume
  vwap: number;
  volume_delta: number;
  volume_spike: VolumeSpikeData;

  // Volatility
  atr: number;
  atr_percent: number;
  bollinger: BollingerBandsData;

  // Composite Scores
  trend_score: number;
  momentum_score: number;
  volatility_score: number;
}

export interface IndicatorResponse {
  success: boolean;
  data: IndicatorSet | null;
  error: string | null;
  cached: boolean;
}

// ---- Signal Classification from Indicators ----

export type SignalClassification = 'strong_buy' | 'buy' | 'neutral' | 'sell' | 'strong_sell';

export interface IndicatorSummary {
  classification: SignalClassification;
  trend: TrendStrengthData;
  momentum: MomentumStrengthData;
  volatility: VolatilityData;
  keyLevels: {
    support: number;
    resistance: number;
  };
}

// ---- Hook State ----

export interface IndicatorState {
  data: IndicatorSet | null;
  loading: boolean;
  error: string | null;
  lastUpdate: number | null;
}

export function classifySignal(indicators: IndicatorSet): SignalClassification {
  let score = 0;

  // Trend contribution
  if (indicators.trend_score > 0.6) score += 2;
  else if (indicators.trend_score > 0.4) score += 1;
  else if (indicators.trend_score < 0.3) score -= 1;

  // RSI contribution
  if (indicators.rsi > 65) score += 1;
  else if (indicators.rsi > 55) score += 0.5;
  else if (indicators.rsi < 35) score -= 1;
  else if (indicators.rsi < 45) score -= 0.5;

  // MACD contribution
  if (indicators.macd.histogram > 0) score += 1;
  else if (indicators.macd.histogram < 0) score -= 1;

  // Volume contribution
  if (indicators.volume_delta > 0) score += 0.5;
  else if (indicators.volume_delta < 0) score -= 0.5;

  if (indicators.volume_spike.is_spike) {
    score += indicators.volume_spike.direction === 'bullish' ? 1 : -1;
  }

  // Classification
  if (score >= 3.5) return 'strong_buy';
  if (score >= 1.5) return 'buy';
  if (score <= -3.5) return 'strong_sell';
  if (score <= -1.5) return 'sell';
  return 'neutral';
}
