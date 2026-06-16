'use client';

import { createContext, useContext, useState, useCallback, useEffect, ReactNode, useRef } from 'react';
import {
  OpenRouterClient,
  getOpenRouterClient,
  resetOpenRouterClient,
} from '@/lib/openrouter';
import type {
  OpenRouterModel,
  OpenRouterSessionStats,
  ConnectionTestResult,
} from '@/types';

interface OpenRouterContextType {
  client: OpenRouterClient;
  apiKey: string;
  modelName: string;
  isConfigured: boolean;
  isTesting: boolean;
  lastTestResult: ConnectionTestResult | null;
  models: OpenRouterModel[];
  isLoadingModels: boolean;
  stats: OpenRouterSessionStats | null;
  setApiKey: (key: string) => void;
  setModel: (model: string) => void;
  testConnection: (model?: string) => Promise<ConnectionTestResult>;
  refreshModels: () => Promise<void>;
  refreshStats: () => void;
  clearHistory: () => void;
}

const OpenRouterContext = createContext<OpenRouterContextType | null>(null);

export function OpenRouterProvider({ children }: { children: ReactNode }) {
  const [client] = useState<OpenRouterClient>(() => {
    const c = getOpenRouterClient();
    const stored = typeof window !== 'undefined' ? localStorage.getItem('openrouter-api-key') : '';
    if (stored && !c.getApiKey()) c.setApiKey(stored);
    const storedModel = typeof window !== 'undefined' ? localStorage.getItem('openrouter-model') : '';
    if (storedModel && !c.getModel()) c.setModel(storedModel);
    return c;
  });
  const [apiKey, setApiKeyState] = useState(() => client.getApiKey());
  const [modelName, setModelName] = useState(() => client.getModel());
  const [isTesting, setIsTesting] = useState(false);
  const [lastTestResult, setLastTestResult] = useState<ConnectionTestResult | null>(null);
  const [models, setModels] = useState<OpenRouterModel[]>([]);
  const [isLoadingModels, setIsLoadingModels] = useState(false);
  const [stats, setStats] = useState<OpenRouterSessionStats | null>(null);
  const refreshIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const isConfigured = apiKey.length > 0 && apiKey.startsWith('sk-or-');

  const setApiKey = useCallback((key: string) => {
    client.setApiKey(key);
    setApiKeyState(key);
    if (typeof window !== 'undefined') localStorage.setItem('openrouter-api-key', key);
  }, [client]);

  const setModel = useCallback((model: string) => {
    client.setModel(model);
    setModelName(model);
    if (typeof window !== 'undefined') localStorage.setItem('openrouter-model', model);
  }, [client]);

  const testConnection = useCallback(async (model?: string): Promise<ConnectionTestResult> => {
    setIsTesting(true);
    try {
      const result = await client.testConnection(model);
      setLastTestResult(result);
      return result;
    } finally {
      setIsTesting(false);
    }
  }, [client]);

  const refreshModels = useCallback(async () => {
    if (!isConfigured) return;
    setIsLoadingModels(true);
    try {
      const fetchedModels = await client.listModels();
      setModels(fetchedModels);
    } catch (error) {
      console.error('Failed to fetch models:', error);
    } finally {
      setIsLoadingModels(false);
    }
  }, [client, isConfigured]);

  const refreshStats = useCallback(() => {
    try {
      const sessionStats = client.getSessionStats();
      setStats(sessionStats);
    } catch {}
  }, [client]);

  const clearHistory = useCallback(() => {
    client.clearCostHistory();
    refreshStats();
  }, [client, refreshStats]);

  // Auto-refresh stats every 5s
  useEffect(() => {
    refreshStats();
    refreshIntervalRef.current = setInterval(refreshStats, 5000);
    return () => {
      if (refreshIntervalRef.current) clearInterval(refreshIntervalRef.current);
    };
  }, [refreshStats]);

  // Fetch models when configured
  useEffect(() => {
    if (isConfigured) {
      refreshModels();
    }
  }, [isConfigured, refreshModels]);

  return (
    <OpenRouterContext.Provider
      value={{
        client,
        apiKey,
        modelName,
        isConfigured,
        isTesting,
        lastTestResult,
        models,
        isLoadingModels,
        stats,
        setApiKey,
        setModel,
        testConnection,
        refreshModels,
        refreshStats,
        clearHistory,
      }}
    >
      {children}
    </OpenRouterContext.Provider>
  );
}

export function useOpenRouter(): OpenRouterContextType {
  const context = useContext(OpenRouterContext);
  if (!context) {
    throw new Error('useOpenRouter must be used within an OpenRouterProvider');
  }
  return context;
}
