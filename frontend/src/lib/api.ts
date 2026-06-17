const API_BASE = 'https://scalmax-1.onrender.com';
const RETRY_DELAYS = [2000, 5000];
const REQUEST_TIMEOUT = 20000;

function getErrorMessage(err: unknown): string {
  if (err instanceof TypeError && err.message === 'Failed to fetch') {
    return 'Backend unreachable (failed to fetch). Is the server running?';
  }
  if (err instanceof DOMException && err.name === 'AbortError') {
    return 'Request timed out. The backend took too long to respond.';
  }
  return err instanceof Error ? err.message : String(err);
}

function isTransientError(err: unknown): boolean {
  const lower = (err instanceof Error ? err.message : String(err)).toLowerCase();
  return lower.includes('429') || lower.includes('too many requests') || lower.includes('rate limit')
    || lower.includes('timeout') || lower.includes('abort')
    || lower.includes('failed to fetch') || lower.includes('network') || lower.includes('econnrefused')
    || lower.includes('502') || lower.includes('503') || lower.includes('service unavailable');
}

async function withRetry<T>(fn: (signal: AbortSignal) => Promise<T>): Promise<T> {
  let lastError: unknown;
  for (let attempt = 0; attempt <= RETRY_DELAYS.length; attempt++) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);
    try {
      const result = await fn(controller.signal);
      clearTimeout(timeoutId);
      return result;
    } catch (err) {
      clearTimeout(timeoutId);
      lastError = err;
      if (attempt < RETRY_DELAYS.length && isTransientError(err)) {
        await new Promise(resolve => setTimeout(resolve, RETRY_DELAYS[attempt]));
      } else {
        break;
      }
    }
  }
  throw new Error(getErrorMessage(lastError));
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

  async analyzeChart(file: File, apiKey: string, model = 'google/gemma-4-31b-it:free', prompt = '', analysisMode = 'quick') {
    return withRetry(async signal => {
      const t_start = performance.now();
      const formData = new FormData()
      formData.append('file', file)
      formData.append('api_key', apiKey.trim())
      formData.append('model', model)
      formData.append('analysis_mode', analysisMode)
      if (prompt) formData.append('prompt', prompt)
      console.log(`[PROFILE] Upload: ${(file.size / 1024).toFixed(0)}KB, model=${model}`);

      const t0 = performance.now();
      const response = await fetch(`${this.baseUrl}/api/v1/vision/analyze`, {
        method: 'POST',
        body: formData,
        signal,
      })
      const t1 = performance.now();
      console.log(`[PROFILE] Backend: HTTP ${response.status}, ${(t1-t0).toFixed(0)}ms`);

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || `HTTP ${response.status}`);
      }

      const t2 = performance.now();
      const result = await response.json() as import('@/types/vision').VisionAnalysisResponse;
      const t3 = performance.now();
      console.log("API RESPONSE", JSON.stringify(result, null, 2));
      console.log(`[PROFILE] Parse: ${(t3-t2).toFixed(0)}ms`);
      if (result.success && result.extraction) {
        console.log(`[PROFILE] Total: ${(t3-t_start).toFixed(0)}ms, bias=${result.extraction.trade.bias}, confidence=${result.extraction.trade.confidence}`);
      }
      return result
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
