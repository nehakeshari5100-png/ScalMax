'use client';

import { useState, useCallback, useRef, useEffect, Component } from 'react';
import { GlassCard } from '@/components/ui/GlassCard';
import { Button } from '@/components/ui/Button';
import { ChartUploader } from '@/components/analysis/ChartUploader';
import type { UploadSource } from '@/components/analysis/ChartUploader';
import { AnalysisResult } from '@/components/analysis/AnalysisResult';
import { useOpenRouter } from '@/lib/openrouter-context';
import { api } from '@/lib/api';
import { Brain, Key, Loader2, AlertTriangle, Layers, Clock } from 'lucide-react';
import type { MarketExtraction, ValidationReport } from '@/types/vision';

const DEFAULT_MODEL = 'google/gemma-4-31b-it:free';
const STAGES = ['Reading chart data...','Compressing image...','Extracting structure...','Analyzing liquidity...','Detecting SMC...','Scanning for FVGs...','Volume & momentum...','Validating signals...','Generating decision...','Finalizing...'];
const SAFETY_TIMEOUT_MS = 90000;

class RawJsonDisplay extends Component<{data:string;error?:string}> {
  render() {
    return (
      <div className="space-y-4">
        {this.props.error && (
          <GlassCard className="p-4 border border-ember-500/30">
            <p className="text-xs font-medium text-ember-400 mb-1">Error: {this.props.error}</p>
          </GlassCard>
        )}
        <GlassCard className="p-4">
          <h3 className="text-xs font-semibold text-cyber-400 mb-2">Raw JSON Response</h3>
          <pre className="text-[10px] text-[var(--color-text-muted)] whitespace-pre-wrap break-all max-h-96 overflow-y-auto font-mono">
            {this.props.data}
          </pre>
        </GlassCard>
      </div>
    );
  }
}

class ResultErrorBoundary extends Component<{children:React.ReactNode;onError?:(e:Error)=>void;rawFallback?:string|null},{error:Error|null}> {
  constructor(p:any) { super(p); this.state = { error: null }; }
  static getDerivedStateFromError(e:Error) { return { error: e }; }
  componentDidCatch(e:Error) { console.error('[RENDER CRASH]', e); this.props.onError?.(e); }
  render() {
    if (this.state.error) {
      return (
        <div className="space-y-4">
          <RawJsonDisplay data={this.state.error.message || String(this.state.error)} error="Render Error" />
          {this.props.rawFallback && <RawJsonDisplay data={this.props.rawFallback} />}
        </div>
      );
    }
    return this.props.children;
  }
}

function SkeletonBlock({ lines=3 }: { lines?: number }) {
  return (
    <GlassCard className="p-5 animate-pulse">
      <div className="space-y-3">
        {Array.from({ length: lines }).map((_, i) => (
          <div key={i} className="h-4 bg-white/5 rounded" style={{ width: `${60 + Math.random() * 30}%` }} />
        ))}
      </div>
    </GlassCard>
  );
}

export default function AnalysisPage() {
  const { apiKey, isConfigured } = useOpenRouter();
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [resolution, setResolution] = useState<{ width: number; height: number } | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [extraction, setExtraction] = useState<MarketExtraction | null>(null);
  const [validation, setValidation] = useState<ValidationReport | null>(null);
  const [usedModel, setUsedModel] = useState('');
  const [progressStage, setProgressStage] = useState(0);
  const [renderError, setRenderError] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const [rawResponse, setRawResponse] = useState<string | null>(null);
  const [showRawJson, setShowRawJson] = useState(false);
  const pasteSourceRef = useRef(false);
  const autoAnalyzeTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const elapsedRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const safetyTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Safety net: force clear analyzing if stuck for 90s
  useEffect(() => {
    if (analyzing) {
      safetyTimerRef.current = setTimeout(() => {
        console.log('[SAFETY] analyzing stuck 90s, force clearing');
        setAnalyzing(false);
        setError('Analysis stuck for 90s. Backend may be unresponsive.');
      }, SAFETY_TIMEOUT_MS);
    }
    return () => { if (safetyTimerRef.current) clearTimeout(safetyTimerRef.current); };
  }, [analyzing]);

  const handleImageReady = useCallback((f: File, p: string, r: { width: number; height: number }, source: UploadSource) => {
    setFile(f);
    setPreview(p);
    setResolution(r);
    setExtraction(null);
    setError(null);
    setRenderError(null);
    setRawResponse(null);
    setShowRawJson(false);
    if (source === 'paste') pasteSourceRef.current = true;
  }, []);

  const handleAnalyze = useCallback(async () => {
    const t0 = performance.now();
    let responseData: any = null;

    try {
      console.log('ANALYSIS START');
      if (!file || !apiKey) { console.log('[PROFILE] Abort: no file or apiKey'); return; }
      if (resolution && (resolution.width < 100 || resolution.height < 100)) {
        setError('Image resolution too low for reliable analysis (minimum 100x100).');
        return;
      }

      setAnalyzing(true);
      setError(null);
      setRenderError(null);
      setRawResponse(null);
      setShowRawJson(false);
      setElapsed(0);
      console.log('LOADING: setAnalyzing(true)');

      elapsedRef.current = setInterval(() => setElapsed((performance.now() - t0) / 1000), 500);

      console.log('RESULT CREATED: calling api.analyzeChart');
      responseData = await api.analyzeChart(file, apiKey, DEFAULT_MODEL, '');
      console.log('API RESPONSE SENT: backend returned', JSON.stringify({
        success: responseData.success,
        hasExtraction: !!responseData.extraction,
        model: responseData.model,
        error: responseData.error,
      }, null, 2));

      console.log('RESULT RECEIVED: processing response');

      if (responseData.success && responseData.extraction) {
        const rawJson = JSON.stringify(responseData, null, 2);
        setRawResponse(rawJson);
        setShowRawJson(true);
        console.log('STATE UPDATED: setting extraction + raw JSON');
        setExtraction(responseData.extraction);
        setValidation(responseData.validation ?? null);
        setUsedModel(responseData.model);
      } else {
        const errMsg = responseData.error || 'Analysis failed';
        const detailStr = responseData.detail
          ? ` [source=${responseData.detail.stage || 'unknown'}, model=${responseData.detail.model || '?'}, originalError=${responseData.detail.originalError || '?'}]`
          : '';
        console.log('STATE UPDATED: setting error', errMsg + detailStr);
        setError(errMsg + detailStr);
        setRawResponse(JSON.stringify(responseData, null, 2));
        setShowRawJson(true);
      }
    } catch (e) {
      const elapsedMs = performance.now() - t0;
      const msg = e instanceof Error ? e.message : String(e);
      console.log('ERROR CAUGHT after ' + elapsedMs.toFixed(0) + 'ms:', msg);
      if (elapsedMs >= 20000 && !msg.toLowerCase().includes('timeout') && !msg.toLowerCase().includes('abort')) {
        setError('The analysis took too long (over 20s). Try a smaller chart image or try again.');
      } else {
        setError(msg);
      }
    } finally {
      console.log('LOADING CLEARED: setAnalyzing(false)');
      setAnalyzing(false);
      if (elapsedRef.current) { clearInterval(elapsedRef.current); elapsedRef.current = null; }
      console.log('[PROFILE] analyzing=false');
    }
  }, [file, apiKey, resolution]);

  // Auto-analyze on paste
  useEffect(() => {
    if (pasteSourceRef.current && file && !analyzing) {
      pasteSourceRef.current = false;
      if (autoAnalyzeTimerRef.current) clearTimeout(autoAnalyzeTimerRef.current);
      autoAnalyzeTimerRef.current = setTimeout(() => { handleAnalyze(); }, 500);
    }
    return () => { if (autoAnalyzeTimerRef.current) clearTimeout(autoAnalyzeTimerRef.current); };
  }, [file, analyzing, handleAnalyze]);

  // Progress stage timer
  useEffect(() => {
    if (!analyzing) { setProgressStage(0); return; }
    const timer = setInterval(() => setProgressStage(prev => Math.min(prev + 1, STAGES.length - 1)), 1500);
    return () => clearInterval(timer);
  }, [analyzing]);

  const handleClear = useCallback(() => {
    setFile(null); setPreview(null); setResolution(null);
    setExtraction(null); setValidation(null); setError(null);
    setRenderError(null); setRawResponse(null); setShowRawJson(false); setElapsed(0);
  }, []);

  const onRenderError = useCallback((e: Error) => { setRenderError(e.message); }, []);
  const finalError = error || renderError;

  return (
    <div className="max-w-6xl mx-auto px-4 lg:px-8 py-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyber-500 to-aurora-700 flex items-center justify-center">
            <Layers className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-bold">Master Extraction Engine</h2>
            <p className="text-xs text-[var(--color-text-muted)]">12-step market structure extraction + trade filter</p>
          </div>
        </div>
      </div>

      {!isConfigured && (
        <GlassCard className="p-6 mb-6 border border-ember-500/20 bg-ember-500/5">
          <div className="flex items-start gap-3">
            <Key className="w-5 h-5 text-ember-400 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-ember-400">OpenRouter API Key Required</p>
              <p className="text-xs text-ember-400/70 mt-1">Go to Settings to configure your OpenRouter API key.</p>
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

          {preview && (
            <GlassCard className="p-5">
              <div className="flex items-center gap-2 mb-3">
                <h3 className="text-sm font-semibold">Chart Preview</h3>
                {resolution && (
                  <span className="text-[10px] text-[var(--color-text-muted)] font-mono">{resolution.width}x{resolution.height}</span>
                )}
              </div>
              <img src={preview} alt="Chart" className="w-full rounded-lg border border-white/5" />
            </GlassCard>
          )}

          <Button variant="primary" className="w-full" size="lg" onClick={handleAnalyze}
            disabled={!file || !apiKey || analyzing} loading={analyzing}>
            {analyzing ? 'Extracting...' : 'Run Extraction'}
          </Button>

          {finalError && (
            <div className="px-4 py-3 rounded-lg bg-ember-500/10 border border-ember-500/20 text-xs text-ember-400">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                {finalError}
              </div>
            </div>
          )}
        </div>

        <div className="lg:col-span-2">
          {analyzing ? (
            <div className="space-y-3">
              <GlassCard className="p-12 flex flex-col items-center justify-center">
                <Loader2 className="w-8 h-8 text-aurora-400 animate-spin mb-4" />
                <div className="w-full max-w-xs bg-white/5 rounded-full h-1.5 mb-4 overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-cyber-400 to-aurora-400 rounded-full transition-all duration-500"
                    style={{ width: `${Math.min(100, ((progressStage + 1) / STAGES.length) * 100)}%` }} />
                </div>
                <p className="text-sm text-[var(--color-text-muted)]">{STAGES[progressStage]}</p>
                <div className="flex items-center gap-1.5 mt-3 text-[10px] text-[var(--color-text-muted)]">
                  <Clock className="w-3 h-3" />
                  {elapsed.toFixed(1)}s
                </div>
              </GlassCard>
              <SkeletonBlock lines={4} />
              <SkeletonBlock lines={3} />
              <SkeletonBlock lines={5} />
            </div>
          ) : showRawJson && rawResponse ? (
            <div className="space-y-4">
              {extraction ? (
                <ResultErrorBoundary onError={onRenderError} rawFallback={rawResponse}>
                  <AnalysisResult extraction={extraction} validation={validation} model={usedModel} />
                </ResultErrorBoundary>
              ) : (
                <RawJsonDisplay data={rawResponse} error={error || undefined} />
              )}
              <GlassCard className="p-3">
                <button onClick={() => setShowRawJson(false)}
                  className="text-[10px] text-cyber-400 hover:text-cyber-300">
                  Hide raw JSON
                </button>
              </GlassCard>
            </div>
          ) : error && rawResponse ? (
            <RawJsonDisplay data={rawResponse} error={error || undefined} />
          ) : (
            <GlassCard className="p-12 flex flex-col items-center justify-center text-center">
              <div className="w-16 h-16 rounded-2xl bg-aurora-500/10 flex items-center justify-center mb-4">
                <Layers className="w-8 h-8 text-aurora-400" />
              </div>
              <p className="text-sm text-[var(--color-text-muted)]">Upload a chart to begin extraction</p>
              <p className="text-xs text-[var(--color-text-muted)] mt-2">
                12-step: detection, structure, liquidity, SMC, FVG, order blocks, premium/discount, volume, momentum, trade filter, plan, scoring
              </p>
            </GlassCard>
          )}
        </div>
      </div>
    </div>
  );
}
