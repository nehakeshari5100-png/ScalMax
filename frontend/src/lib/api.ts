const API_BASE = 'https://scalmax-1.onrender.com';
const RETRY_DELAYS = [2000, 5000, 10000];
const REQUEST_TIMEOUT = 60000;

function sanitizeError(err: unknown): string {
  if (err instanceof TypeError && err.message === 'Failed to fetch') {
    return 'Analysis temporarily unavailable. Backend is waking up. Retrying...';
  }
  if (err instanceof DOMException && err.name === 'AbortError') {
    return 'Analysis timed out. The backend took too long to respond. Retrying...';
  }
  const msg = err instanceof Error ? err.message : String(err);
  const lower = msg.toLowerCase();
  if (lower.includes('429') || lower.includes('too many requests') || lower.includes('rate limit')) {
    return 'Analysis temporarily unavailable. Retrying...';
  }
  if (lower.includes('401') || lower.includes('unauthorized') || lower.includes('invalid api key') || lower.includes('authentication')) {
    return 'Analysis temporarily unavailable. Retrying...';
  }
  if (lower.includes('404') || lower.includes('not found') || lower.includes('502') || lower.includes('503') || lower.includes('service unavailable') || lower.includes('bad gateway')) {
    return 'Analysis temporarily unavailable. Retrying...';
  }
  if (lower.includes('402') || lower.includes('insufficient credits') || lower.includes('quota') || lower.includes('payment')) {
    return 'Analysis temporarily unavailable. Retrying...';
  }
  if (lower.includes('provider') || lower.includes('upstream') || lower.includes('origin')) {
    return 'Analysis temporarily unavailable. Retrying...';
  }
  if (msg.length > 120) {
    return 'Analysis temporarily unavailable. Retrying...';
  }
  return msg;
}

async function withRetry<T>(fn: (signal: AbortSignal) => Promise<T>): Promise<T> {
  for (let attempt = 0; attempt <= RETRY_DELAYS.length; attempt++) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);
    try {
      const result = await fn(controller.signal);
      clearTimeout(timeoutId);
      return result;
    } catch (err) {
      clearTimeout(timeoutId);
      const friendly = sanitizeError(err);
      if (attempt === RETRY_DELAYS.length) {
        throw new Error(friendly);
      }
      await new Promise(resolve => setTimeout(resolve, RETRY_DELAYS[attempt]));
    }
  }
  throw new Error('Analysis temporarily unavailable. Please retry shortly.');
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    return withRetry(async signal => {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...(options.headers as Record<string, string>),
        },
        signal,
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || `HTTP ${response.status}`);
      }
      return response.json();
    });
  }

  async analyzeChart(file: File, apiKey: string, model = 'nex-agi/nex-n2-pro:free', prompt = '', analysisMode = 'quick') {
    return withRetry(async signal => {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('api_key', apiKey.trim())
      formData.append('model', model)
      formData.append('analysis_mode', analysisMode)
      if (prompt) formData.append('prompt', prompt)

      const response = await fetch(`${this.baseUrl}/api/v1/vision/analyze`, {
        method: 'POST',
        body: formData,
        signal,
      })

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || `HTTP ${response.status}`);
      }

      return response.json() as Promise<import('@/types/vision').VisionAnalysisResponse>
    })
  }

  async getVisionHealth() {
    return this.request<{ status: string; service: string }>('/api/v1/vision/health')
  }

  async getHealth() {
    return this.request<{ status: string; version: string }>('/api/health')
  }
}

export const api = new ApiClient(API_BASE);
export default api;
