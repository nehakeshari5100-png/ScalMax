import type {
  OpenRouterModel,
  OpenRouterChatMessage,
  OpenRouterChatRequest,
  OpenRouterChatResponse,
  OpenRouterStreamChunk,
  OpenRouterCostEntry,
  OpenRouterSessionStats,
  ConnectionTestResult,
} from '@/types';
import { api } from './api';

const OPENROUTER_BASE = 'https://openrouter.ai/api/v1';
const OPENROUTER_REFERRER = 'scalpex-ai';

const MODEL_PRICING: Record<string, { prompt: number; completion: number }> = {
  'google/gemma-3-12b-it': { prompt: 0.00000020, completion: 0.00000020 },
  'openai/gpt-4o-mini': { prompt: 0.00000015, completion: 0.00000060 },
  'openai/gpt-4o': { prompt: 0.00000250, completion: 0.00001000 },
  'anthropic/claude-3.5-sonnet': { prompt: 0.00000300, completion: 0.00001500 },
  'deepseek/deepseek-chat': { prompt: 0.00000014, completion: 0.00000028 },
};

class TokenBucket {
  private capacity: number;
  private tokens: number;
  private refillRate: number;
  private lastRefill: number;

  constructor(capacity: number, refillRate: number) {
    this.capacity = capacity;
    this.tokens = capacity;
    this.refillRate = refillRate;
    this.lastRefill = Date.now();
  }

  private refill(): void {
    const now = Date.now();
    const elapsed = (now - this.lastRefill) / 1000;
    this.tokens = Math.min(this.capacity, this.tokens + elapsed * this.refillRate);
    this.lastRefill = now;
  }

  tryConsume(count: number = 1): boolean {
    this.refill();
    if (this.tokens >= count) {
      this.tokens -= count;
      return true;
    }
    return false;
  }

  waitTime(): number {
    this.refill();
    if (this.tokens >= 1) return 0;
    return ((1 - this.tokens) / this.refillRate) * 1000;
  }
}

interface RetryOptions {
  maxRetries: number;
  baseDelayMs: number;
  maxDelayMs: number;
  jitter: boolean;
}

async function withRetry<T>(
  fn: () => Promise<T>,
  options: Partial<RetryOptions> = {}
): Promise<T> {
  const { maxRetries = 3, baseDelayMs = 1000, maxDelayMs = 10000, jitter = true } = options;
  let lastError: Error | null = null;
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));
      if (attempt === maxRetries) break;
      if (error instanceof ResponseError && error.status >= 400 && error.status < 500 && error.status !== 429) break;
      const delay = Math.min(baseDelayMs * Math.pow(2, attempt), maxDelayMs);
      const jitterMs = jitter ? Math.random() * 200 : 0;
      await new Promise(resolve => setTimeout(resolve, delay + jitterMs));
    }
  }
  throw lastError;
}

class ResponseError extends Error {
  status: number;
  body: unknown;
  constructor(message: string, status: number, body?: unknown) {
    super(message);
    this.name = 'ResponseError';
    this.status = status;
    this.body = body;
  }
}

class CostTracker {
  private history: OpenRouterCostEntry[] = [];
  private sessionId: string;

  constructor() {
    this.sessionId = this.loadSessionId();
    this.history = this.loadHistory();
  }

  private loadSessionId(): string {
    try {
      const stored = sessionStorage.getItem('scalpex_or_session');
      if (stored) return stored;
    } catch {}
    const id = `session_${Date.now()}_${Math.random().toString(36).substring(2, 8)}`;
    try { sessionStorage.setItem('scalpex_or_session', id); } catch {}
    return id;
  }

  private loadHistory(): OpenRouterCostEntry[] {
    try {
      const stored = sessionStorage.getItem('scalpex_or_costs');
      if (stored) return JSON.parse(stored);
    } catch {}
    return [];
  }

  private persist(): void {
    try {
      sessionStorage.setItem('scalpex_or_costs', JSON.stringify(this.history.slice(-1000)));
    } catch {}
  }

  record(model: string, promptTokens: number, completionTokens: number, pricing: { prompt: number; completion: number }): OpenRouterCostEntry {
    const promptCost = (promptTokens / 1000) * pricing.prompt;
    const completionCost = (completionTokens / 1000) * pricing.completion;
    const entry: OpenRouterCostEntry = {
      model, timestamp: Date.now(), promptTokens, completionTokens,
      totalTokens: promptTokens + completionTokens, promptCost, completionCost,
      totalCost: promptCost + completionCost, sessionId: this.sessionId,
    };
    this.history.push(entry);
    this.persist();
    return entry;
  }

  getSessionStats(): OpenRouterSessionStats {
    const sessionEntries = this.history.filter(e => e.sessionId === this.sessionId);
    const totalCost = sessionEntries.reduce((s, e) => s + e.totalCost, 0);
    const totalTokens = sessionEntries.reduce((s, e) => s + e.totalTokens, 0);
    const totalRequests = sessionEntries.length;
    const modelBreakdown: Record<string, { requests: number; cost: number; tokens: number }> = {};
    for (const entry of sessionEntries) {
      if (!modelBreakdown[entry.model]) modelBreakdown[entry.model] = { requests: 0, cost: 0, tokens: 0 };
      modelBreakdown[entry.model].requests++;
      modelBreakdown[entry.model].cost += entry.totalCost;
      modelBreakdown[entry.model].tokens += entry.totalTokens;
    }
    return { totalCost, totalTokens, totalRequests, averageTokensPerRequest: totalRequests > 0 ? totalTokens / totalRequests : 0, modelBreakdown, costHistory: sessionEntries.slice(-50) };
  }

  clearHistory(): void {
    this.history = [];
    this.persist();
  }

  getHistory(): OpenRouterCostEntry[] {
    return this.history;
  }
}

export class OpenRouterClient {
  private apiKey: string = '';
  private modelName: string;
  private rateLimiter: TokenBucket;
  private costTracker: CostTracker;

  constructor(apiKey?: string, modelName?: string) {
    this.apiKey = apiKey || '';
    this.modelName = modelName || 'nex-agi/nex-n2-pro:free';
    this.rateLimiter = new TokenBucket(60, 30);
    this.costTracker = new CostTracker();
  }

  setApiKey(key: string): void {
    this.apiKey = key;
  }

  setModel(model: string): void {
    this.modelName = model;
  }

  getApiKey(): string {
    return this.apiKey;
  }

  getModel(): string {
    return this.modelName;
  }

  hasValidKey(): boolean {
    return this.apiKey.length > 0 && this.apiKey.startsWith('sk-or-');
  }

  private getPricing(model: string): { prompt: number; completion: number } {
    return MODEL_PRICING[model] || { prompt: 0.00000050, completion: 0.00000050 };
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    if (!this.apiKey) throw new Error('OpenRouter API key not configured. Set it in Settings.');
    const url = `${OPENROUTER_BASE}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json',
        'HTTP-Referer': OPENROUTER_REFERRER,
        'X-Title': 'Scalpex AI',
        ...options.headers,
      },
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      const errorMessage = body.error?.message || body.message || `OpenRouter API error: ${response.status}`;
      throw new ResponseError(errorMessage, response.status, body);
    }
    return response.json();
  }

  async listModels(): Promise<OpenRouterModel[]> {
    return withRetry(async () => {
      const data = await this.request<{ data: OpenRouterModel[] }>('/models');
      return data.data.filter(m => m.architecture.modality === 'text' || m.architecture.modality === 'text+image').sort((a, b) => a.name.localeCompare(b.name));
    }, { maxRetries: 2 });
  }

  async chat(messages: OpenRouterChatMessage[], options: Partial<OpenRouterChatRequest> = {}): Promise<OpenRouterChatResponse> {
    return withRetry(async () => {
      if (!this.rateLimiter.tryConsume(1)) await new Promise(resolve => setTimeout(resolve, this.rateLimiter.waitTime()));
      const requestBody: OpenRouterChatRequest = { model: options.model || this.modelName, messages, temperature: options.temperature ?? 0.7, top_p: options.top_p ?? 0.9, max_tokens: options.max_tokens ?? 1024, stream: false, ...options };
      const response = await this.request<OpenRouterChatResponse>('/chat/completions', { method: 'POST', body: JSON.stringify(requestBody) });
      if (response.usage) this.costTracker.record(response.model, response.usage.prompt_tokens, response.usage.completion_tokens, this.getPricing(response.model));
      return response;
    }, { maxRetries: 3 });
  }

  async chatStream(messages: OpenRouterChatMessage[], options: Partial<OpenRouterChatRequest> & { onChunk?: (chunk: OpenRouterStreamChunk) => void; onDone?: (fullContent: string, usage?: { prompt_tokens: number; completion_tokens: number; total_tokens: number }) => void; onError?: (error: Error) => void; signal?: AbortSignal } = {}): Promise<string> {
    const controller = new AbortController();
    const signal = options.signal || controller.signal;
    try {
      if (!this.rateLimiter.tryConsume(1)) await new Promise(resolve => setTimeout(resolve, this.rateLimiter.waitTime()));
      const requestBody: OpenRouterChatRequest = { model: options.model || this.modelName, messages, temperature: options.temperature ?? 0.7, top_p: options.top_p ?? 0.9, max_tokens: options.max_tokens ?? 4096, stream: true, ...options };
      const response = await fetch(`${OPENROUTER_BASE}/chat/completions`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${this.apiKey}`, 'Content-Type': 'application/json', 'HTTP-Referer': OPENROUTER_REFERRER, 'X-Title': 'Scalpex AI' },
        body: JSON.stringify(requestBody),
        signal,
      });
      if (!response.ok) { const body = await response.json().catch(() => ({})); throw new ResponseError(body.error?.message || `Stream error: ${response.status}`, response.status, body); }
      const reader = response.body?.getReader();
      if (!reader) throw new Error('Response body is not readable');
      const decoder = new TextDecoder();
      let fullContent = '';
      let lastUsage: { prompt_tokens: number; completion_tokens: number; total_tokens: number } | undefined;
      const processLine = (line: string) => {
        if (!line || line.startsWith(':')) return;
        if (line === 'data: [DONE]') return;
        if (line.startsWith('data: ')) {
          try {
            const chunk: OpenRouterStreamChunk = JSON.parse(line.slice(6));
            const content = chunk.choices?.[0]?.delta?.content || '';
            fullContent += content;
            if (chunk.usage) lastUsage = chunk.usage;
            options.onChunk?.(chunk);
          } catch {}
        }
      };
      let buffer = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        for (const line of lines) processLine(line.trim());
      }
      if (buffer.trim()) processLine(buffer.trim());
      if (lastUsage) this.costTracker.record(options.model || this.modelName, lastUsage.prompt_tokens, lastUsage.completion_tokens, this.getPricing(options.model || this.modelName));
      else {
        const estimatedCompletionTokens = Math.ceil(fullContent.length / 4);
        const estimatedPromptTokens = messages.reduce((s, m) => s + Math.ceil(m.content.length / 4), 0);
        this.costTracker.record(options.model || this.modelName, estimatedPromptTokens, estimatedCompletionTokens, this.getPricing(options.model || this.modelName));
      }
      options.onDone?.(fullContent, lastUsage);
      return fullContent;
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      options.onError?.(err);
      throw err;
    }
  }

  async testConnection(model?: string): Promise<ConnectionTestResult> {
    const startTime = Date.now();
    const testModel = model || this.modelName;
    try {
      const response = await withRetry(async () => this.chat([{ role: 'user', content: 'Reply with exactly: OK' }], { model: testModel, max_tokens: 10, temperature: 0 }), { maxRetries: 2, baseDelayMs: 500 });
      return { success: true, latency: Date.now() - startTime, model: response.model || testModel };
    } catch (error) {
      return { success: false, latency: Date.now() - startTime, model: testModel, error: error instanceof Error ? error.message : 'Connection failed' };
    }
  }

  getSessionStats(): OpenRouterSessionStats { return this.costTracker.getSessionStats(); }
  getCostHistory(): OpenRouterCostEntry[] { return this.costTracker.getHistory(); }
  clearCostHistory(): void { this.costTracker.clearHistory(); }
}

const DEFAULT_API_KEY = typeof process !== 'undefined'
  ? (process.env.NEXT_PUBLIC_OPENROUTER_API_KEY || '')
  : '';

let clientInstance: OpenRouterClient | null = null;

export function getOpenRouterClient(): OpenRouterClient {
  if (!clientInstance) clientInstance = new OpenRouterClient(DEFAULT_API_KEY);
  return clientInstance;
}

export function resetOpenRouterClient(key?: string, model?: string): OpenRouterClient {
  clientInstance = new OpenRouterClient(key, model);
  return clientInstance;
}

export default getOpenRouterClient;
