const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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
      credentials: 'include',
    });

    if (response.status === 401) {
      if (typeof window !== 'undefined' && !endpoint.includes('/auth/')) {
        document.cookie = 'scalpex_token=; path=/; max-age=0';
        window.location.href = '/login?redirect=' + encodeURIComponent(window.location.pathname);
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
    if (token) {
      document.cookie = `scalpex_token=${encodeURIComponent(token)}; path=/; max-age=3600; SameSite=Strict; Secure`;
    } else {
      document.cookie = 'scalpex_token=; path=/; max-age=0; SameSite=Strict; Secure';
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

  // Market
  async getTokens(): Promise<import('@/types').Token[]> {
    return this.request('/api/market/tokens');
  }

  async getCandles(symbol: string, timeframe: string, limit?: number) {
    const params = new URLSearchParams({ timeframe });
    if (limit) params.set('limit', limit.toString());
    return this.request(`/api/market/candles/${symbol}?${params}`);
  }

  async getOrderBook(symbol: string) {
    return this.request(`/api/market/orderbook/${symbol}`);
  }

  // Signals
  async getSignals(params?: { status?: string; symbol?: string; limit?: number }) {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set('status', params.status);
    if (params?.symbol) searchParams.set('symbol', params.symbol);
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    const qs = searchParams.toString();
    return this.request(`/api/signals${qs ? `?${qs}` : ''}`);
  }

  // Journal
  async getTrades(params?: { status?: string; symbol?: string; limit?: number }) {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set('status', params.status);
    if (params?.symbol) searchParams.set('symbol', params.symbol);
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    const qs = searchParams.toString();
    return this.request(`/api/journal/trades${qs ? `?${qs}` : ''}`);
  }

  // Analytics
  async getPortfolioStats() {
    return this.request('/api/analytics/portfolio');
  }

  async getPerformanceMetrics() {
    return this.request('/api/analytics/performance');
  }

  // Scanner
  async getScannerResults() {
    return this.request('/api/scanner/results');
  }

  // Liquidity Engine
  async getLiquidityMap(params: { symbol: string; timeframe?: string; exchange?: string; lookback?: number }) {
    return this.request<import('@/types/liquidity').LiquidityResponse>(
      '/api/v1/liquidity/map',
      { method: 'POST', body: JSON.stringify(params) }
    )
  }

  async getLiquidityHealth() {
    return this.request<{ status: string; service: string }>('/api/v1/liquidity/health')
  }

  // Confluence Scoring Engine
  async getConfluenceScore(params: { symbol: string; timeframe?: string; exchange?: string; data: import('@/types/confluence').ConfluenceInput }) {
    return this.request<import('@/types/confluence').ScoreResponse>(
      '/api/v1/confluence/score',
      { method: 'POST', body: JSON.stringify(params) }
    )
  }

  async getConfluenceHealth() {
    return this.request<{ status: string; service: string }>('/api/v1/confluence/health')
  }

  // Calibration Engine
  async calibrateScores(scores: number[]) {
    return this.request<import('@/types/calibration').CalibrateResponse>(
      '/api/v1/calibration/calibrate',
      { method: 'POST', body: JSON.stringify({ scores }) }
    )
  }

  async recordTradeOutcome(params: import('@/types/calibration').RecordTradeRequest) {
    return this.request<import('@/types/calibration').CalibrateResponse>(
      '/api/v1/calibration/record',
      { method: 'POST', body: JSON.stringify(params) }
    )
  }

  async getCalibrationStats(minSamples = 10) {
    return this.request<import('@/types/calibration').CalibrationStatsResponse>(
      `/api/v1/calibration/stats?min_samples=${minSamples}`
    )
  }

  async clearCalibrationData() {
    return this.request<{ success: boolean; message: string }>(
      '/api/v1/calibration/clear',
      { method: 'POST' }
    )
  }

  async getCalibrationHealth() {
    return this.request<{ status: string; service: string }>('/api/v1/calibration/health')
  }

  // Backtesting Engine
  async runBacktest(params: import('@/types/backtesting').BacktestRunRequest) {
    return this.request<import('@/types/backtesting').BacktestRunResponse>(
      '/api/v1/backtesting/run',
      { method: 'POST', body: JSON.stringify(params) }
    )
  }

  async getBacktestResults(params?: { symbol?: string; timeframe?: string; strategy_version?: string; limit?: number; offset?: number }) {
    const sp = new URLSearchParams()
    if (params?.symbol) sp.set('symbol', params.symbol)
    if (params?.timeframe) sp.set('timeframe', params.timeframe)
    if (params?.strategy_version) sp.set('strategy_version', params.strategy_version)
    if (params?.limit) sp.set('limit', params.limit.toString())
    if (params?.offset) sp.set('offset', params.offset.toString())
    const qs = sp.toString()
    return this.request<import('@/types/backtesting').BacktestListResponse>(
      `/api/v1/backtesting/results${qs ? `?${qs}` : ''}`
    )
  }

  async getBacktestResult(rid: string) {
    return this.request<import('@/types/backtesting').BacktestRunResponse>(
      `/api/v1/backtesting/results/${rid}`
    )
  }

  async deleteBacktestResult(rid: string) {
    return this.request<{ success: boolean; message: string }>(
      `/api/v1/backtesting/results/${rid}`,
      { method: 'DELETE' }
    )
  }

  async getBacktestReportUrl(rid: string) {
    return `${this.baseUrl}/api/v1/backtesting/report/${rid}`
  }

  async getBacktestSupported() {
    return this.request<import('@/types/backtesting').SupportedOptions>(
      '/api/v1/backtesting/supported'
    )
  }

  async getBacktestHealth() {
    return this.request<{ status: string; service: string }>('/api/v1/backtesting/health')
  }

  // Vision Analysis Engine
  async analyzeChart(file: File, apiKey: string, model = 'google/gemma-3-27b-it', prompt = '') {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('api_key', apiKey)
    formData.append('model', model)
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

  // Master AI Decision Engine
  async makeDecision(params: import('@/types/decision').DecisionInput) {
    return this.request<import('@/types/decision').DecisionResponse>(
      '/api/v1/decision/decide',
      { method: 'POST', body: JSON.stringify(params) }
    )
  }

  async getDecisionHealth() {
    return this.request<{ status: string; service: string }>('/api/v1/decision/health')
  }

  // Signal Engine
  async generateSignal(params: import('@/types/signals').SignalCreateRequest) {
    return this.request<import('@/types/signals').SignalResponse>(
      '/api/v1/signals/generate',
      { method: 'POST', body: JSON.stringify(params) }
    )
  }

  async listSignals(params?: { symbol?: string; timeframe?: string; signal_type?: string; status?: string; direction?: string; min_confidence?: number; search?: string; page?: number; page_size?: number }) {
    const sp = new URLSearchParams()
    if (params?.symbol) sp.set('symbol', params.symbol)
    if (params?.timeframe) sp.set('timeframe', params.timeframe)
    if (params?.signal_type) sp.set('signal_type', params.signal_type)
    if (params?.status) sp.set('status', params.status)
    if (params?.direction) sp.set('direction', params.direction)
    if (params?.min_confidence) sp.set('min_confidence', params.min_confidence.toString())
    if (params?.search) sp.set('search', params.search)
    if (params?.page) sp.set('page', params.page.toString())
    if (params?.page_size) sp.set('page_size', params.page_size.toString())
    const qs = sp.toString()
    return this.request<import('@/types/signals').SignalListResponse>(
      `/api/v1/signals/signals${qs ? `?${qs}` : ''}`
    )
  }

  async getSignal(id: string) {
    return this.request<import('@/types/signals').SignalResponse>(`/api/v1/signals/signals/${id}`)
  }

  async updateSignal(id: string, params: import('@/types/signals').SignalUpdateRequest) {
    return this.request<import('@/types/signals').SignalResponse>(
      `/api/v1/signals/signals/${id}`,
      { method: 'PATCH', body: JSON.stringify(params) }
    )
  }

  async deleteSignal(id: string) {
    return this.request<{ success: boolean; message: string }>(
      `/api/v1/signals/signals/${id}`,
      { method: 'DELETE' }
    )
  }

  async getSignalPerformance(params?: { symbol?: string; timeframe?: string }) {
    const sp = new URLSearchParams()
    if (params?.symbol) sp.set('symbol', params.symbol)
    if (params?.timeframe) sp.set('timeframe', params.timeframe)
    const qs = sp.toString()
    return this.request<import('@/types/signals').SignalPerformanceResponse>(
      `/api/v1/signals/performance${qs ? `?${qs}` : ''}`
    )
  }

  async getSignalHealth() {
    return this.request<{ status: string; service: string }>('/api/v1/signals/health')
  }

  // Integration Pipeline
  async runPipeline(params: import('@/types/integration').PipelineRequest) {
    return this.request<import('@/types/integration').PipelineResponse>(
      '/api/v1/pipeline/run',
      { method: 'POST', body: JSON.stringify(params) }
    )
  }

  async quickAnalysis(params: import('@/types/integration').PipelineRequest) {
    return this.request<import('@/types/integration').PipelineResponse>(
      '/api/v1/pipeline/quick',
      { method: 'POST', body: JSON.stringify(params) }
    )
  }

  async getPipelineHealth() {
    return this.request<{ status: string; service: string }>('/api/v1/pipeline/health')
  }

  // Paper Trading
  async createPaperAccount(params: import('@/types/papertrading').CreateAccountRequest) {
    return this.request<import('@/types/papertrading').AccountResponse>(
      '/api/v1/papertrading/accounts',
      { method: 'POST', body: JSON.stringify(params) }
    )
  }

  async listPaperAccounts() {
    return this.request<import('@/types/papertrading').AccountListResponse>('/api/v1/papertrading/accounts')
  }

  async getPaperAccount(accountId: string) {
    return this.request<import('@/types/papertrading').AccountResponse>(
      `/api/v1/papertrading/accounts/${accountId}`
    )
  }

  async deletePaperAccount(accountId: string) {
    return this.request<import('@/types/papertrading').AccountResponse>(
      `/api/v1/papertrading/accounts/${accountId}`,
      { method: 'DELETE' }
    )
  }

  async openPaperPosition(params: import('@/types/papertrading').OpenPositionRequest) {
    return this.request<import('@/types/papertrading').PositionResponse>(
      '/api/v1/papertrading/positions',
      { method: 'POST', body: JSON.stringify(params) }
    )
  }

  async listPaperPositions(params?: { account_id?: string; status?: string; symbol?: string; direction?: string; signal_id?: string; limit?: number; offset?: number }) {
    const sp = new URLSearchParams()
    if (params?.account_id) sp.set('account_id', params.account_id)
    if (params?.status) sp.set('status', params.status)
    if (params?.symbol) sp.set('symbol', params.symbol)
    if (params?.direction) sp.set('direction', params.direction)
    if (params?.signal_id) sp.set('signal_id', params.signal_id)
    if (params?.limit) sp.set('limit', params.limit.toString())
    if (params?.offset) sp.set('offset', params.offset.toString())
    const qs = sp.toString()
    return this.request<import('@/types/papertrading').PositionListResponse>(
      `/api/v1/papertrading/positions${qs ? `?${qs}` : ''}`
    )
  }

  async getPaperPosition(positionId: string) {
    return this.request<import('@/types/papertrading').PositionResponse>(
      `/api/v1/papertrading/positions/${positionId}`
    )
  }

  async closePaperPosition(positionId: string, params: import('@/types/papertrading').ClosePositionRequest) {
    return this.request<import('@/types/papertrading').PositionResponse>(
      `/api/v1/papertrading/positions/${positionId}/close`,
      { method: 'POST', body: JSON.stringify(params) }
    )
  }

  async cancelPaperPosition(positionId: string) {
    return this.request<import('@/types/papertrading').PositionResponse>(
      `/api/v1/papertrading/positions/${positionId}/cancel`,
      { method: 'POST' }
    )
  }

  async getPaperPositionFills(positionId: string) {
    return this.request<{ success: boolean; data: import('@/types/papertrading').TradeFill[] }>(
      `/api/v1/papertrading/positions/${positionId}/fills`
    )
  }

  async getPaperStats(accountId: string) {
    return this.request<import('@/types/papertrading').StatsResponse>(
      `/api/v1/papertrading/stats/${accountId}`
    )
  }

  async getPaperLeaderboard(limit?: number) {
    const qs = limit ? `?limit=${limit}` : ''
    return this.request<import('@/types/papertrading').LeaderboardResponse>(
      `/api/v1/papertrading/leaderboard${qs}`
    )
  }

  async checkPaperPositions(accountId: string, currentPrice: number, symbol?: string) {
    const sp = new URLSearchParams()
    sp.set('account_id', accountId)
    sp.set('current_price', currentPrice.toString())
    if (symbol) sp.set('symbol', symbol)
    return this.request<{ success: boolean; closed: Record<string, unknown>[] }>(
      `/api/v1/papertrading/check-positions?${sp.toString()}`,
      { method: 'POST' }
    )
  }

  async peekPrice(symbol: string, exchange?: string) {
    return this.request<{ success: boolean; price: number | null; error: string | null }>(
      '/api/v1/papertrading/peek-price',
      { method: 'POST', body: JSON.stringify({ symbol, exchange: exchange || 'binance' }) }
    )
  }

  async getPaperTradingHealth() {
    return this.request<{ status: string; service: string }>('/api/v1/papertrading/health')
  }
}

export const api = new ApiClient(API_BASE);
export default api;
