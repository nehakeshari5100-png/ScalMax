'use client';

import { useRef, useCallback } from 'react';
import { cn } from '@/lib/utils';
import { Zap } from 'lucide-react';

interface CameraCaptureProps {
  onCapture: (file: File, preview: string) => void;
  disabled?: boolean;
}

export function CameraCapture({ onCapture, disabled }: CameraCaptureProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const handleCapture = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      const dataUrl = ev.target?.result as string;
      onCapture(file, dataUrl);
    };
    reader.readAsDataURL(file);
    if (inputRef.current) inputRef.current.value = '';
  }, [onCapture]);

  return (
    <>
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        capture="environment"
        className="hidden"
        onChange={handleCapture}
        disabled={disabled}
      />
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        disabled={disabled}
        className={cn(
          'flex items-center justify-center gap-2 w-full py-3 px-4 rounded-xl border border-dashed text-sm font-medium transition-all',
          'border-white/10 hover:border-white/20 bg-surface-elevated/30 hover:bg-surface-elevated/50',
          'disabled:opacity-40 disabled:cursor-not-allowed'
        )}
      >
        <Zap className="w-5 h-5" />
        <span>Capture with Camera</span>
      </button>
    </>
  );
}
