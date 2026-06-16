const API_BASE = 'https://scalmax-1.onrender.com';
const RETRY_DELAYS = [2000, 5000];
const REQUEST_TIMEOUT = 30000;

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
      console.log('[PIPELINE] Step 1: Image upload - building FormData');
      const formData = new FormData()
      formData.append('file', file)
      formData.append('api_key', apiKey.trim())
      formData.append('model', model)
      formData.append('analysis_mode', analysisMode)
      if (prompt) formData.append('prompt', prompt)
      console.log(`[PIPELINE] Step 1 done. File size: ${(file.size / 1024).toFixed(1)}KB, model: ${model}`);

      console.log('[PIPELINE] Step 2: Sending request to backend');
      const t0 = performance.now();
      const response = await fetch(`${this.baseUrl}/api/v1/vision/analyze`, {
        method: 'POST',
        body: formData,
        signal,
      })
      const t1 = performance.now();
      console.log(`[PIPELINE] Step 2 done. HTTP ${response.status}, took ${(t1-t0).toFixed(0)}ms`);

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        console.log(`[PIPELINE] Step 2 FAILED: ${body.detail || `HTTP ${response.status}`}`);
        throw new Error(body.detail || `HTTP ${response.status}`);
      }

      console.log('[PIPELINE] Step 3: Parsing response');
      const result = await response.json() as import('@/types/vision').VisionAnalysisResponse;
      console.log(`[PIPELINE] Step 3 done. success=${result.success}, model=${result.model}, error=${result.error}`);
      if (result.success && result.extraction) {
        console.log(`[PIPELINE] Complete: extraction bias=${result.extraction.trade.bias}, confidence=${result.extraction.trade.confidence}`);
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
