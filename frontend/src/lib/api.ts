const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers as Record<string, string>),
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `API Error: ${response.status}`);
    }

    return response.json();
  }

  // Vision Analysis
  async analyzeChart(file: File, apiKey: string, model = 'openrouter/free', prompt = '', analysisMode = 'quick') {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('api_key', apiKey)
    formData.append('model', model)
    formData.append('analysis_mode', analysisMode)
    if (prompt) formData.append('prompt', prompt)

    const response = await fetch(`${this.baseUrl}/api/v1/vision/analyze`, {
      method: 'POST',
      body: formData,
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
