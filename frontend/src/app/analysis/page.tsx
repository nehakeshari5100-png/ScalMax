'use client';

import { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import { PageContainer } from '@/components/layout/PageContainer';
import { GlassCard } from '@/components/ui/GlassCard';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { ChartUploader } from '@/components/analysis/ChartUploader';
import { AnalysisResult } from '@/components/analysis/AnalysisResult';
import { useOpenRouter } from '@/lib/openrouter-context';
import { api } from '@/lib/api';
import { Brain, Key, Loader2, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';
import type { ChartAnalysisResult } from '@/types/vision';

export default function AnalysisPage() {
  const { apiKey, modelName, isConfigured, setApiKey, setModel } = useOpenRouter();

  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [resolution, setResolution] = useState<{ width: number; height: number } | null>(null);
  const [localModel, setLocalModel] = useState(modelName);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ChartAnalysisResult | null>(null);
  const [usedModel, setUsedModel] = useState('');

  const handleImageReady = useCallback((f: File, p: string, r: { width: number; height: number }) => {
    setFile(f);
    setPreview(p);
    setResolution(r);
    setResult(null);
    setError(null);
  }, []);

  const handleClear = useCallback(() => {
    setFile(null);
    setPreview(null);
    setResolution(null);
    setResult(null);
    setError(null);
  }, []);

  const handleAnalyze = async () => {
    if (!file || !apiKey) return;
    setAnalyzing(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.analyzeChart(file, apiKey, localModel);
      if (res.success && res.data) {
        if (res.data.direction === 'NO_TRADE' && res.data.confidence === 0) {
          setError('Chart quality too low for reliable analysis.');
        } else {
          setResult(res.data);
          setUsedModel(res.model);
        }
      } else {
        setError(res.error || 'Analysis failed');
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Analysis request failed');
    } finally {
      setAnalyzing(false);
    }
  };

  const models = [
    'google/gemma-3-27b-it',
    'google/gemma-3-12b-it',
    'google/gemma-3-vision',
    'google/gemini-2.0-flash-001',
    'openai/gpt-4o-mini',
  ];

  return (
    <PageContainer>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyber-500 to-aurora-700 flex items-center justify-center">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-bold">Chart Analysis</h2>
            <p className="text-xs text-[var(--color-text-muted)]">
              Upload a chart screenshot for AI-powered scalping analysis
            </p>
          </div>
        </div>
      </div>

      {!isConfigured && (
        <GlassCard className="p-6 mb-6 border border-ember-500/20 bg-ember-500/5">
          <div className="flex items-start gap-3">
            <Key className="w-5 h-5 text-ember-400 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-ember-400">OpenRouter API Key Required</p>
              <p className="text-xs text-ember-400/70 mt-1">
                Go to Settings to configure your OpenRouter API key before using chart analysis.
              </p>
            </div>
          </div>
        </GlassCard>
      )}

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-5">
          <GlassCard className="p-5">
            <div className="flex items-center gap-2 mb-4">
              <Brain className="w-4 h-4 text-cyber-400" />
              <h3 className="text-sm font-semibold">Upload Chart</h3>
            </div>
            <ChartUploader onImageReady={handleImageReady} onClear={handleClear} disabled={analyzing} />
          </GlassCard>

          <GlassCard className="p-5">
            <div className="flex items-center gap-2 mb-4">
              <Brain className="w-4 h-4 text-cyber-400" />
              <h3 className="text-sm font-semibold">Vision Model</h3>
            </div>
            <div className="space-y-3">
              <select
                value={localModel}
                onChange={(e) => setLocalModel(e.target.value)}
                className="glass-input w-full py-2.5 px-3 text-sm"
              >
                {models.map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
              <p className="text-[10px] text-[var(--color-text-muted)]">
                Select a vision-capable model for chart analysis.
              </p>
            </div>
          </GlassCard>

          {preview && (
            <GlassCard className="p-5">
              <div className="flex items-center gap-2 mb-3">
                <h3 className="text-sm font-semibold">Chart Preview</h3>
                {resolution && (
                  <span className="text-[10px] text-[var(--color-text-muted)] font-mono">
                    {resolution.width}x{resolution.height}
                  </span>
                )}
              </div>
              <img src={preview} alt="Chart" className="w-full rounded-lg border border-white/5" />
            </GlassCard>
          )}

          <Button
            variant="primary"
            className="w-full"
            size="lg"
            onClick={handleAnalyze}
            disabled={!file || !apiKey || analyzing}
            loading={analyzing}
          >
            {analyzing ? 'Analyzing...' : 'Run Analysis'}
          </Button>

          {error && (
            <div className="flex items-center gap-2 px-4 py-3 rounded-lg bg-ember-500/10 border border-ember-500/20 text-xs text-ember-400">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              {error}
            </div>
          )}
        </div>

        <div className="lg:col-span-2">
          {analyzing ? (
            <GlassCard className="p-12 flex flex-col items-center justify-center">
              <Loader2 className="w-8 h-8 text-aurora-400 animate-spin mb-4" />
              <p className="text-sm text-[var(--color-text-muted)]">Sending chart to OpenRouter for analysis...</p>
              <p className="text-xs text-[var(--color-text-muted)] mt-2">This may take 15-30 seconds</p>
            </GlassCard>
          ) : result ? (
            <AnalysisResult data={result} model={usedModel} />
          ) : (
            <GlassCard className="p-12 flex flex-col items-center justify-center text-center">
              <div className="w-16 h-16 rounded-2xl bg-aurora-500/10 flex items-center justify-center mb-4">
                <Brain className="w-8 h-8 text-aurora-400" />
              </div>
              <p className="text-sm text-[var(--color-text-muted)]">
                Upload a chart screenshot to get started
              </p>
              <p className="text-xs text-[var(--color-text-muted)] mt-2">
                Drag & drop, click to upload, or paste (Ctrl+V) a TradingView screenshot
              </p>
            </GlassCard>
          )}
        </div>
      </div>
    </PageContainer>
  );
}
