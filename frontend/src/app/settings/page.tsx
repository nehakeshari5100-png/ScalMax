'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';
import { GlassCard } from '@/components/ui/GlassCard';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useOpenRouter } from '@/lib/openrouter-context';
import {
  Settings, Key, Brain, Bot, Save, AlertTriangle,
  Eye, EyeOff, Activity, DollarSign, BarChart3, Clock, Trash2, CheckCircle, XCircle,
  Loader2, Copy
} from 'lucide-react';
import type { ConnectionTestResult, OpenRouterCostEntry } from '@/types';

export default function SettingsPage() {
  const {
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
    clearHistory,
    refreshStats,
  } = useOpenRouter();

  const [localKey, setLocalKey] = useState(apiKey);
  const [localModel, setLocalModel] = useState(modelName);
  const [showApiKey, setShowApiKey] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [testResult, setTestResult] = useState<ConnectionTestResult | null>(lastTestResult);
  const [isTestingNow, setIsTestingNow] = useState(false);
  const [activeTab, setActiveTab] = useState<'config' | 'stats' | 'history'>('config');
  const [costHistory, setCostHistory] = useState<OpenRouterCostEntry[]>([]);

  const keyIsValid = localKey.startsWith('sk-or-');
  const keyChanged = localKey !== apiKey;
  const modelChanged = localModel !== modelName;

  useEffect(() => {
    if (stats) {
      setCostHistory(client.getCostHistory());
    }
  }, [stats, client]);

  const handleSave = useCallback(() => {
    setIsSaving(true);
    setSaveMessage(null);
    setTimeout(() => {
      try {
        setApiKey(localKey);
        setModel(localModel);
        setSaveMessage({ type: 'success', text: 'Settings saved.' });
        setIsSaving(false);
        refreshStats();
        if (keyChanged && keyIsValid) {
          refreshModels();
        }
      } catch (error) {
        setSaveMessage({ type: 'error', text: error instanceof Error ? error.message : 'Failed to save settings' });
        setIsSaving(false);
      }
    }, 600);
  }, [localKey, localModel, setApiKey, setModel, refreshStats, keyChanged, keyIsValid, refreshModels]);

  const handleTestConnection = useCallback(async () => {
    if (!keyIsValid) {
      setTestResult({ success: false, latency: 0, model: localModel, error: 'Invalid API key format.' });
      return;
    }
    setIsTestingNow(true);
    const result = await testConnection(localModel);
    setTestResult(result);
    setIsTestingNow(false);
  }, [keyIsValid, localModel, testConnection]);

  const handleClearHistory = useCallback(() => {
    clearHistory();
    setCostHistory([]);
  }, [clearHistory]);

  const formatCost = (cost: number): string => {
    if (cost < 0.0001) return '$0.0000';
    if (cost < 0.01) return `$${(cost ?? 0).toFixed(5)}`;
    if (cost < 1) return `$${(cost ?? 0).toFixed(4)}`;
    return `$${(cost ?? 0).toFixed(3)}`;
  };

  const formatTokens = (tokens: number): string => {
    if (tokens >= 1_000_000) return `${((tokens ?? 0) / 1_000_000).toFixed(2)}M`;
    if (tokens >= 1_000) return `${((tokens ?? 0) / 1_000).toFixed(1)}K`;
    return tokens.toString();
  };

  return (
    <div className="max-w-6xl mx-auto px-4 lg:px-8 py-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-aurora-500 to-aurora-700 flex items-center justify-center">
            <Settings className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-bold">Settings</h2>
            <p className="text-xs text-[var(--color-text-muted)]">Configure OpenRouter API and model</p>
          </div>
        </div>
        <Button
          variant={saveMessage?.type === 'success' ? 'primary' : 'secondary'}
          size="sm"
          icon={isSaving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
          onClick={handleSave}
          disabled={isSaving}
        >
          {isSaving ? 'Saving...' : 'Save'}
        </Button>
      </div>

      <AnimatePresence>
        {saveMessage && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className={cn(
              'flex items-center gap-2 px-4 py-3 rounded-lg mb-6 text-sm border',
              saveMessage.type === 'success'
                ? 'bg-aurora-500/10 border-aurora-500/20 text-aurora-400'
                : 'bg-red-500/10 border-red-500/20 text-red-400'
            )}
          >
            {saveMessage.type === 'success' ? <CheckCircle className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
            {saveMessage.text}
          </motion.div>
        )}
      </AnimatePresence>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {[
          { label: 'API Status', value: isConfigured ? 'Configured' : 'Not Set', icon: Key, color: isConfigured ? 'text-aurora-400' : 'text-ember-400', bg: isConfigured ? 'bg-aurora-500/10' : 'bg-ember-500/10' },
          { label: 'Active Model', value: modelName.split('/').pop()?.replace(/-/g, ' ') || 'None', icon: Brain, color: 'text-cyber-400', bg: 'bg-cyber-500/10' },
          { label: 'Session Cost', value: stats ? formatCost(stats.totalCost) : '$0.0000', icon: DollarSign, color: 'text-aurora-400', bg: 'bg-aurora-500/10' },
          { label: 'Total Requests', value: stats ? stats.totalRequests.toString() : '0', icon: Activity, color: 'text-[var(--color-text)]', bg: 'bg-surface-elevated/60' },
        ].map((stat, i) => {
          const Icon = stat.icon;
          return (
            <motion.div key={stat.label} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}>
              <GlassCard>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="stat-label">{stat.label}</p>
                    <p className={cn('stat-value mt-1 text-sm', stat.color)}>{stat.value}</p>
                  </div>
                  <div className={cn('w-9 h-9 rounded-lg flex items-center justify-center', stat.bg)}>
                    <Icon className={cn('w-4 h-4', stat.color)} />
                  </div>
                </div>
              </GlassCard>
            </motion.div>
          );
        })}
      </div>

      <div className="flex items-center gap-1 mb-6 border-b border-white/5">
        {[
          { id: 'config' as const, label: 'Configuration', icon: Settings },
          { id: 'stats' as const, label: 'Usage Stats', icon: BarChart3 },
          { id: 'history' as const, label: 'Cost History', icon: Clock },
        ].map(tab => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors border-b-2 -mb-[1px]',
                activeTab === tab.id ? 'text-aurora-400 border-aurora-400' : 'text-[var(--color-text-muted)] border-transparent hover:text-[var(--color-text)]'
              )}
            >
              <Icon className="w-4 h-4" />{tab.label}
            </button>
          );
        })}
      </div>

      {activeTab === 'config' && (
        <div className="max-w-xl">
          <GlassCard className="p-6 space-y-6">
            <div className="flex items-center gap-2 pb-4 border-b border-white/5">
              <Brain className="w-5 h-5 text-cyber-400" />
              <h3 className="text-base font-semibold">OpenRouter AI Configuration</h3>
              <Badge variant="info" size="sm">Required</Badge>
            </div>

            <div>
              <label className="block text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider mb-1.5">API Key</label>
              <div className="relative">
                <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)]" />
                <input
                  type={showApiKey ? 'text' : 'password'}
                  value={localKey}
                  onChange={e => setLocalKey(e.target.value)}
                  className={cn('glass-input w-full pl-10 pr-10 py-2.5 font-mono text-sm', localKey && !keyIsValid && 'border-red-500/50')}
                  placeholder="sk-or-v1-..."
                />
                <div className="absolute right-2 top-1/2 -translate-y-1/2">
                  <button onClick={() => setShowApiKey(!showApiKey)} className="p-1.5 text-[var(--color-text-muted)] hover:text-[var(--color-text)] rounded">
                    {showApiKey ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>
              <div className="flex items-center justify-between mt-1">
                <p className="text-[10px] text-[var(--color-text-muted)]">
                  {keyIsValid ? 'Valid format' : localKey ? 'Key should start with sk-or-' : 'Required for AI analysis'}
                </p>
                {localKey && (
                  <button onClick={() => navigator.clipboard.writeText(localKey)} className="text-[10px] text-aurora-400 hover:text-aurora-300 flex items-center gap-1">
                    <Copy className="w-2.5 h-2.5" /> Copy
                  </button>
                )}
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider mb-1.5">AI Model</label>
              <div className="relative">
                <Bot className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)] z-10" />
                <select value={localModel} onChange={e => setLocalModel(e.target.value)} className="glass-input w-full pl-10 py-2.5 text-sm">
                  <optgroup label="Free Models">
                    <option value="openrouter/free">OpenRouter Free Router ($0)</option>
                    <option value="google/gemma-3-12b-it:free">Gemma 3 12B (free)</option>
                    <option value="google/gemma-3-4b-it:free">Gemma 3 4B (free)</option>
                    <option value="nvidia/nemotron-nano-12b-v2-vl:free">Nemotron Nano 12B VL (free)</option>
                  </optgroup>
                  {isLoadingModels ? (
                    <option disabled>Loading models...</option>
                  ) : models.length > 0 ? (
                    <optgroup label={`${models.length} models available`}>
                      {models.map(m => (<option key={m.id} value={m.id}>{m.name} ({m.id})</option>))}
                    </optgroup>
                  ) : null}
                  <optgroup label="Paid Models">
                    <option value="google/gemma-3-27b-it">Gemma 3 27B</option>
                    <option value="google/gemma-3-vision">Gemma 3 Vision</option>
                    <option value="google/gemma-3-12b-it">Gemma 3 12B</option>
                    <option value="google/gemini-2.0-flash-001">Gemini 2.0 Flash</option>
                    <option value="openai/gpt-4o-mini">GPT-4o Mini</option>
                    <option value="deepseek/deepseek-chat">DeepSeek Chat</option>
                  </optgroup>
                </select>
                {isLoadingModels && <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 animate-spin text-aurora-400" />}
              </div>
            </div>

            <div className="glass rounded-xl p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium flex items-center gap-2">
                  <Activity className="w-4 h-4 text-cyber-400" /> Connection Test
                </span>
                <Button variant="secondary" size="sm" icon={isTestingNow ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null} onClick={handleTestConnection} disabled={isTestingNow || !keyIsValid}>
                  {isTestingNow ? 'Testing...' : 'Test'}
                </Button>
              </div>
              <AnimatePresence>
                {testResult && (
                  <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
                    className={cn('p-3 rounded-lg text-sm border', testResult.success ? 'bg-aurora-500/10 border-aurora-500/20' : 'bg-red-500/10 border-red-500/20')}>
                    {testResult.success ? (
                      <div className="space-y-1">
                        <div className="flex items-center gap-2 text-aurora-400 font-medium"><CheckCircle className="w-4 h-4" /> Connected</div>
                        <div className="grid grid-cols-2 gap-2 mt-2 text-xs">
                          <div><span className="text-[var(--color-text-muted)]">Model:</span> <span className="font-mono">{testResult.model}</span></div>
                          <div><span className="text-[var(--color-text-muted)]">Latency:</span> <span className="font-mono">{testResult.latency}ms</span></div>
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-1">
                        <div className="flex items-center gap-2 text-red-400 font-medium"><XCircle className="w-4 h-4" /> Failed</div>
                        <p className="text-xs text-red-400/80 mt-1">{testResult.error}</p>
                      </div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            <div className="flex items-start gap-2 p-3 rounded-lg bg-amber-500/5 border border-amber-500/10">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
              <div>
                <p className="text-xs text-amber-400/80 font-medium">Security</p>
                <p className="text-[10px] text-amber-400/60 mt-0.5">API key stored in localStorage. Never shared outside OpenRouter.</p>
              </div>
            </div>
          </GlassCard>
        </div>
      )}

      {activeTab === 'stats' && (
        <div className="space-y-6">
          {stats && stats.totalRequests > 0 ? (
            <>
              <GlassCard className="p-6">
                <h3 className="text-base font-semibold flex items-center gap-2 mb-6">
                  <BarChart3 className="w-5 h-5 text-aurora-400" /> Session Usage
                </h3>
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
                  <div><p className="stat-label">Total Cost</p><p className="stat-value text-aurora-400 mt-1">{formatCost(stats.totalCost)}</p></div>
                  <div><p className="stat-label">Total Tokens</p><p className="stat-value mt-1">{formatTokens(stats.totalTokens)}</p></div>
                  <div><p className="stat-label">Avg / Request</p><p className="stat-value mt-1">{Math.round(stats.averageTokensPerRequest).toLocaleString()}</p></div>
                  <div><p className="stat-label">Requests</p><p className="stat-value mt-1">{stats.totalRequests}</p></div>
                </div>
              </GlassCard>
              {Object.keys(stats.modelBreakdown).length > 0 && (
                <GlassCard className="p-6">
                  <h3 className="text-base font-semibold mb-4 flex items-center gap-2"><Brain className="w-5 h-5 text-cyber-400" /> Model Breakdown</h3>
                  <div className="space-y-3">
                    {Object.entries(stats.modelBreakdown).map(([model, data]) => (
                      <div key={model} className="glass-card p-4 flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium">{model.split('/').pop()?.replace(/-/g, ' ')}</p>
                          <p className="text-xs text-[var(--color-text-muted)] font-mono mt-0.5">{model}</p>
                        </div>
                        <div className="flex items-center gap-6">
                          <div className="text-right"><p className="text-xs text-[var(--color-text-muted)]">Req</p><p className="text-sm font-mono font-medium">{data.requests}</p></div>
                          <div className="text-right"><p className="text-xs text-[var(--color-text-muted)]">Tokens</p><p className="text-sm font-mono font-medium">{formatTokens(data.tokens)}</p></div>
                          <div className="text-right"><p className="text-xs text-[var(--color-text-muted)]">Cost</p><p className="text-sm font-mono font-medium text-aurora-400">{formatCost(data.cost)}</p></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </GlassCard>
              )}
            </>
          ) : (
            <GlassCard className="flex flex-col items-center justify-center py-16 text-center">
              <Activity className="w-12 h-12 text-[var(--color-text-muted)] mb-3" />
              <p className="text-sm text-[var(--color-text-muted)]">No usage data yet</p>
            </GlassCard>
          )}
        </div>
      )}

      {activeTab === 'history' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-[var(--color-text-secondary)]">{costHistory.length} entries</p>
            <Button variant="danger" size="sm" icon={<Trash2 className="w-3.5 h-3.5" />} onClick={handleClearHistory}>Clear</Button>
          </div>
          {costHistory.length > 0 ? (
            <GlassCard className="p-0 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-white/5">
                      <th className="text-left text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider px-4 py-3">Time</th>
                      <th className="text-left text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider px-4 py-3">Model</th>
                      <th className="text-right text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider px-4 py-3">Prompt</th>
                      <th className="text-right text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider px-4 py-3">Completion</th>
                      <th className="text-right text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider px-4 py-3">Total</th>
                      <th className="text-right text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider px-4 py-3">Cost</th>
                    </tr>
                  </thead>
                  <tbody>
                    {costHistory.slice().reverse().map((entry, i) => (
                      <motion.tr key={`${entry.timestamp}-${i}`} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.01 }}
                        className="border-b border-white/5 last:border-0 hover:bg-white/[0.02] transition-colors">
                        <td className="px-4 py-3 text-xs font-mono text-[var(--color-text-muted)]">{new Date(entry.timestamp).toLocaleTimeString()}</td>
                        <td className="px-4 py-3 text-xs font-medium">{entry.model.split('/').pop()?.replace(/-/g, ' ')}</td>
                        <td className="px-4 py-3 text-xs font-mono text-right">{entry.promptTokens.toLocaleString()}</td>
                        <td className="px-4 py-3 text-xs font-mono text-right">{entry.completionTokens.toLocaleString()}</td>
                        <td className="px-4 py-3 text-xs font-mono text-right">{entry.totalTokens.toLocaleString()}</td>
                        <td className="px-4 py-3 text-xs font-mono text-right text-aurora-400">{formatCost(entry.totalCost)}</td>
                      </motion.tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </GlassCard>
          ) : (
            <GlassCard className="flex flex-col items-center justify-center py-16 text-center">
              <Clock className="w-12 h-12 text-[var(--color-text-muted)] mb-3" />
              <p className="text-sm text-[var(--color-text-muted)]">No cost history</p>
            </GlassCard>
          )}
        </div>
      )}
    </div>
  );
}
