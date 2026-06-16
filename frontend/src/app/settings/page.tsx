'use client';

import { useState, useCallback } from 'react';
import { GlassCard } from '@/components/ui/GlassCard';
import { Button } from '@/components/ui/Button';
import { useOpenRouter } from '@/lib/openrouter-context';
import {
  Settings, Key, Save, AlertTriangle,
  Eye, EyeOff, CheckCircle, XCircle, Loader2, Copy
} from 'lucide-react';

export default function SettingsPage() {
  const { apiKey, setApiKey } = useOpenRouter();
  const [localKey, setLocalKey] = useState(apiKey);
  const [showApiKey, setShowApiKey] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const keyIsValid = localKey.startsWith('sk-or-');
  const keyChanged = localKey !== apiKey;

  const handleSave = useCallback(() => {
    setIsSaving(true);
    setSaveMessage(null);
    setTimeout(() => {
      try {
        setApiKey(localKey);
        setSaveMessage({ type: 'success', text: 'Settings saved.' });
        setIsSaving(false);
      } catch (error) {
        setSaveMessage({ type: 'error', text: error instanceof Error ? error.message : 'Failed to save settings' });
        setIsSaving(false);
      }
    }, 600);
  }, [localKey, setApiKey]);

  return (
    <div className="max-w-6xl mx-auto px-4 lg:px-8 py-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-aurora-500 to-aurora-700 flex items-center justify-center">
            <Settings className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-bold">Settings</h2>
            <p className="text-xs text-[var(--color-text-muted)]">Configure your API key</p>
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

      {saveMessage && (
        <div
          className={'flex items-center gap-2 px-4 py-3 rounded-lg mb-6 text-sm border ' + (saveMessage.type === 'success'
            ? 'bg-aurora-500/10 border-aurora-500/20 text-aurora-400'
            : 'bg-red-500/10 border-red-500/20 text-red-400')}
        >
          {saveMessage.type === 'success' ? <CheckCircle className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
          {saveMessage.text}
        </div>
      )}

      <div className="max-w-xl">
        <GlassCard className="p-6 space-y-6">
          <div className="flex items-center gap-2 pb-4 border-b border-white/5">
            <Key className="w-5 h-5 text-cyber-400" />
            <h3 className="text-base font-semibold">API Key</h3>
          </div>

          <div>
            <label className="block text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider mb-1.5">
              OpenRouter API Key
            </label>
            <div className="relative">
              <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)]" />
              <input
                type={showApiKey ? 'text' : 'password'}
                value={localKey}
                onChange={e => setLocalKey(e.target.value)}
                className={'glass-input w-full pl-10 pr-10 py-2.5 font-mono text-sm' + (localKey && !keyIsValid ? ' border-red-500/50' : '')}
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

          <div className="flex items-start gap-2 p-3 rounded-lg bg-amber-500/5 border border-amber-500/10">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <div>
              <p className="text-xs text-amber-400/80 font-medium">Security</p>
              <p className="text-[10px] text-amber-400/60 mt-0.5">API key stored in localStorage. Never shared outside OpenRouter.</p>
            </div>
          </div>
        </GlassCard>
      </div>
    </div>
  );
}