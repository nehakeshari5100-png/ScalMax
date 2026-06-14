'use client';

import { cn } from '@/lib/utils';

interface BadgeProps {
  variant?: 'default' | 'long' | 'short' | 'neutral' | 'success' | 'warning' | 'danger' | 'info';
  size?: 'sm' | 'md';
  children: React.ReactNode;
  className?: string;
  pulse?: boolean;
}

const variants = {
  default: 'bg-surface-elevated/60 text-[var(--color-text-secondary)] border-white/5',
  long: 'bg-green-500/15 text-green-400 border-green-500/20',
  short: 'bg-red-500/15 text-red-400 border-red-500/20',
  neutral: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/20',
  success: 'bg-aurora-500/15 text-aurora-400 border-aurora-500/20',
  warning: 'bg-ember-500/15 text-ember-400 border-ember-500/20',
  danger: 'bg-red-500/15 text-red-400 border-red-500/20',
  info: 'bg-cyber-500/15 text-cyber-400 border-cyber-500/20',
};

export function Badge({ variant = 'default', size = 'sm', children, className, pulse }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border font-medium',
        size === 'sm' ? 'px-2.5 py-0.5 text-xs' : 'px-3 py-1 text-sm',
        variants[variant],
        pulse && 'animate-pulse',
        className
      )}
    >
      {variant === 'long' && <span className="w-1.5 h-1.5 rounded-full bg-green-400" />}
      {variant === 'short' && <span className="w-1.5 h-1.5 rounded-full bg-red-400" />}
      {variant === 'success' && <span className="w-1.5 h-1.5 rounded-full bg-aurora-400" />}
      {variant === 'warning' && <span className="w-1.5 h-1.5 rounded-full bg-ember-400 animate-pulse" />}
      {variant === 'danger' && <span className="w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse" />}
      {children}
    </span>
  );
}
