const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

class ApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async getToken(): Promise<string | null> {
    if (this.token) return this.token;
    if (typeof document === 'undefined') return null;
    const match = document.cookie.match(/(?:^|;\s*)scalpex_token=([^;]*)/);
    return match ? decodeURIComponent(match[1]) : null;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    const token = await this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      if (typeof window !== 'undefined' && endpoint !== '/api/auth/login') {
        document.cookie = 'scalpex_token=; path=/; max-age=0';
        window.location.href = '/login';
      }
      throw new Error('Authentication required');
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `API Error: ${response.status}`);
    }

    return response.json();
  }

  setToken(token: string | null) {
    this.token = token;
    const secure = typeof window !== 'undefined' && window.location.protocol === 'https:' ? '; Secure' : '';
    if (token) {
      document.cookie = `scalpex_token=${encodeURIComponent(token)}; path=/; max-age=3600; SameSite=Strict${secure}`;
    } else {
      document.cookie = `scalpex_token=; path=/; max-age=0; SameSite=Strict${secure}`;
    }
  }

  // Auth
  async login(password: string): Promise<{ token: string }> {
    const res = await this.request<{ token: string }>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ password }),
    });
    this.setToken(res.token);
    return res;
  }

  async logout() {
    this.setToken(null);
  }

  async getOpenRouterKey(): Promise<{ api_key: string }> {
    return this.request('/api/auth/openrouter-key');
  }

  // Settings
  async getSettings() {
    return this.request('/api/settings');
  }

  async updateSettings(settings: Record<string, unknown>) {
    return this.request('/api/settings', {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  }

  // Vision Analysis
  async analyzeChart(file: File, apiKey: string, model = 'openrouter/free', prompt = '', analysisMode = 'quick') {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('api_key', apiKey)
    formData.append('model', model)
    formData.append('analysis_mode', analysisMode)
    if (prompt) formData.append('prompt', prompt)

    const token = await this.getToken()
    const response = await fetch(`${this.baseUrl}/api/v1/vision/analyze`, {
      method: 'POST',
      body: formData,
      headers: token ? { 'Authorization': `Bearer ${token}` } : {},
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(error.detail || `Vision API Error: ${response.status}`)
    }

    return response.json() as Promise<import('@/types/vision').VisionAnalysisResponse>
  }

  async getVisionModels() {
    return this.request<import('@/types/vision').VisionModelsResponse>('/api/v1/vision/models')
  }

  async getVisionHealth() {
    return this.request<{ status: string; service: string }>('/api/v1/vision/health')
  }

  // Health
  async getHealth() {
    return this.request<{ status: string; version: string }>('/api/health')
  }
}

export const api = new ApiClient(API_BASE);
export default api;
