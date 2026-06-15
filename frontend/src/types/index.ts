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
  choices: { index: number; message: OpenRouterChatMessage; finish_reason: 'stop' | 'length' | 'error' | null }[];
  usage: { prompt_tokens: number; completion_tokens: number; total_tokens: number };
}

export interface OpenRouterStreamChunk {
  id: string;
  model: string;
  choices: { index: number; delta: { role?: string; content?: string }; finish_reason: 'stop' | 'length' | null }[];
  usage?: { prompt_tokens: number; completion_tokens: number; total_tokens: number };
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
