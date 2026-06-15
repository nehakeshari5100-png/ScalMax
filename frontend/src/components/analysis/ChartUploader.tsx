'use client';

import { useState, useRef, useCallback, useEffect, DragEvent, ClipboardEvent } from 'react';
import { cn } from '@/lib/utils';
import { Upload, Eye, XCircle, AlertTriangle } from 'lucide-react';
import { CameraCapture } from './CameraCapture';

export type UploadSource = 'drag' | 'click' | 'paste' | 'camera';

const ALLOWED_TYPES = ['image/png', 'image/jpeg', 'image/webp'];
const MAX_SIZE = 20 * 1024 * 1024;

interface ChartUploaderProps {
  onImageReady: (file: File, preview: string, resolution: { width: number; height: number }, source: UploadSource) => void;
  onClear: () => void;
  disabled?: boolean;
}

export function ChartUploader({ onImageReady, onClear, disabled }: ChartUploaderProps) {
  const [dragOver, setDragOver] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [resolution, setResolution] = useState<{ width: number; height: number } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateAndLoad = useCallback((file: File, source: UploadSource) => {
    setError(null);
    if (!ALLOWED_TYPES.includes(file.type)) {
      setError(`Unsupported format. Use PNG, JPG, or WEBP.`);
      return;
    }
    if (file.size > MAX_SIZE) {
      setError(`File too large (${(file.size / 1024 / 1024).toFixed(1)}MB). Max 20MB.`);
      return;
    }
    setFileName(file.name);
    const reader = new FileReader();
    reader.onload = (e) => {
      const dataUrl = e.target?.result as string;
      const img = new Image();
      img.onload = () => {
        const res = { width: img.naturalWidth, height: img.naturalHeight };
        setResolution(res);
        setPreview(dataUrl);
        onImageReady(file, dataUrl, res, source);
      };
      img.src = dataUrl;
    };
    reader.readAsDataURL(file);
  }, [onImageReady]);

  const handleDrop = useCallback((e: DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) validateAndLoad(file, 'drag');
  }, [validateAndLoad]);

  const handlePaste = useCallback((e: ClipboardEvent) => {
    const items = e.clipboardData?.items;
    if (!items) return;
    const arr = Array.from(items);
    for (const item of arr) {
      if (item.type.startsWith('image/')) {
        const file = item.getAsFile();
        if (file) { validateAndLoad(file, 'paste'); break; }
      }
    }
  }, [validateAndLoad]);

  const handleCameraCapture = useCallback((file: File, preview: string) => {
    const img = new Image();
    img.onload = () => {
      const res = { width: img.naturalWidth, height: img.naturalHeight };
      setResolution(res);
      setPreview(preview);
      setFileName(file.name);
      onImageReady(file, preview, res, 'camera');
    };
    img.src = preview;
  }, [onImageReady]);

  useEffect(() => {
    const handler = (e: Event) => {
      const ce = e as unknown as ClipboardEvent;
      const target = e.target as HTMLElement;
      if (target.closest('[data-uploader]')) return;
      const items = ce.clipboardData?.items;
      if (!items) return;
      const arr = Array.from(items);
      for (const item of arr) {
        if (item.type.startsWith('image/')) {
          const file = item.getAsFile();
          if (file) {
            validateAndLoad(file, 'paste');
            break;
          }
        }
      }
    };
    document.addEventListener('paste', handler);
    return () => document.removeEventListener('paste', handler);
  }, [validateAndLoad]);

  const handleClear = () => {
    setPreview(null);
    setResolution(null);
    setError(null);
    setFileName(null);
    if (inputRef.current) inputRef.current.value = '';
    onClear();
  };

  return (
    <div data-uploader className="space-y-4">
      {!preview ? (
        <div
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          className={cn(
            'relative border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all',
            dragOver
              ? 'border-aurora-400 bg-aurora-500/5'
              : 'border-white/10 hover:border-white/20 bg-surface-elevated/30'
          )}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".png,.jpg,.jpeg,.webp"
            className="hidden"
            onChange={(e) => { const f = e.target.files?.[0]; if (f) validateAndLoad(f, 'click'); }}
          />
          <div className="flex flex-col items-center gap-3">
            <div className="w-14 h-14 rounded-xl bg-aurora-500/10 flex items-center justify-center">
              <Upload className="w-6 h-6 text-aurora-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-[var(--color-text)]">
                Drop chart screenshot or click to upload
              </p>
              <p className="text-xs text-[var(--color-text-muted)] mt-1">
                PNG, JPG, WEBP — Max 20MB — Ctrl+V to paste
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="relative rounded-xl overflow-hidden border border-white/5 bg-surface-elevated/30">
          <img src={preview} alt="Chart preview" className="w-full h-auto max-h-64 object-contain" />
          <div className="absolute inset-x-0 bottom-0 flex items-center justify-between px-4 py-2 bg-gradient-to-t from-black/80 to-transparent">
            <div className="flex items-center gap-2 text-xs text-white/70">
              <Eye className="w-3.5 h-3.5" />
              <span>{fileName}</span>
              {resolution && (
                <span className="text-white/50">{resolution.width}x{resolution.height}</span>
              )}
            </div>
            <button onClick={handleClear} disabled={disabled} className="p-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-white/70 hover:text-white transition-colors">
              <XCircle className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {!preview && (
        <CameraCapture onCapture={handleCameraCapture} disabled={disabled} />
      )}

      {error && (
        <div className="flex items-center gap-2 px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/20 text-xs text-red-400">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      )}
    </div>
  );
}
