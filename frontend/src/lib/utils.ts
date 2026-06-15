import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPrice(price: number, decimals?: number): string {
  if (price === 0) return '$0.00';
  const d = decimals ?? (price < 0.01 ? 6 : price < 1 ? 4 : price < 100 ? 2 : 2);
  return '$' + (price ?? 0).toFixed(d);
}

export function formatPriceRaw(price: number, decimals?: number): string {
  if (price === 0) return '0.00';
  const d = decimals ?? (price < 0.01 ? 6 : price < 1 ? 4 : price < 100 ? 2 : 2);
  return (price ?? 0).toFixed(d);
}

export function formatVolume(volume: number): string {
  if (volume >= 1_000_000_000) return ((volume ?? 0) / 1_000_000_000).toFixed(2) + 'B';
  if (volume >= 1_000_000) return ((volume ?? 0) / 1_000_000).toFixed(2) + 'M';
  if (volume >= 1_000) return ((volume ?? 0) / 1_000).toFixed(2) + 'K';
  return (volume ?? 0).toFixed(2);
}

export function formatPercent(value: number): string {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${(value ?? 0).toFixed(2)}%`;
}

export function formatTimestamp(ts: number, format: 'time' | 'date' | 'datetime' | 'relative' = 'datetime'): string {
  const date = new Date(ts);
  if (format === 'relative') {
    const diff = Date.now() - ts;
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  }
  if (format === 'time') return date.toLocaleTimeString('en-US', { hour12: false });
  if (format === 'date') return date.toLocaleDateString('en-US');
  return date.toLocaleString('en-US', { hour12: false });
}

export function generateId(): string {
  return Math.random().toString(36).substring(2, 15) + Date.now().toString(36);
}

export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export function debounce<T extends (...args: unknown[]) => unknown>(fn: T, ms: number): (...args: Parameters<T>) => void {
  let timer: ReturnType<typeof setTimeout>;
  return (...args: Parameters<T>) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), ms);
  };
}


