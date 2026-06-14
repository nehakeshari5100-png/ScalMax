'use client';

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import { ReactNode } from 'react';

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  glow?: 'green' | 'blue' | 'amber' | 'none';
  padding?: 'sm' | 'md' | 'lg';
  onClick?: () => void;
}

export function GlassCard({ children, className, hover = true, glow = 'none', padding = 'md', onClick }: GlassCardProps) {
  const glowStyles = {
    green: 'hover:shadow-glow',
    blue: 'hover:shadow-glow-blue',
    amber: 'hover:shadow-glow-amber',
    none: '',
  };

  const paddingStyles = {
    sm: 'p-3',
    md: 'p-5',
    lg: 'p-7',
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className={cn(
        'glass rounded-xl border border-white/5',
        hover && 'glass-hover',
        glowStyles[glow],
        paddingStyles[padding],
        onClick && 'cursor-pointer',
        className
      )}
      onClick={onClick}
    >
      {children}
    </motion.div>
  );
}

export function GlassPanel({ children, className, ...props }: GlassCardProps) {
  return (
    <GlassCard className={cn('rounded-2xl', className)} padding="lg" {...props}>
      {children}
    </GlassCard>
  );
}
