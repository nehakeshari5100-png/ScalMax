'use client';

import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import { ButtonHTMLAttributes, forwardRef } from 'react';
import { Loader2 } from 'lucide-react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  icon?: React.ReactNode;
}

const variants = {
  primary: 'glass-button-primary',
  secondary: 'glass-button-secondary',
  danger: 'glass-button-danger',
  ghost: 'glass-button bg-transparent text-[var(--color-text-secondary)] hover:text-[var(--color-text)] hover:bg-white/5 active:scale-[0.98]',
  outline: 'glass-button bg-transparent border border-surface-border text-[var(--color-text-secondary)] hover:text-[var(--color-text)] hover:border-white/20 active:scale-[0.98]',
};

const sizes = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-5 py-2.5 text-sm',
  lg: 'px-7 py-3 text-base',
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', size = 'md', loading, icon, children, className, disabled, ...props }, ref) => {
    return (
      <motion.button
        ref={ref}
        whileHover={{ scale: disabled || loading ? 1 : 1.01 }}
        whileTap={{ scale: disabled || loading ? 1 : 0.98 }}
        className={cn(variants[variant], sizes[size], disabled && 'opacity-50 cursor-not-allowed', className)}
        disabled={disabled || loading}
        {...(props as React.ComponentProps<typeof motion.button>)}
      >
        {loading ? (
          <Loader2 className="w-4 h-4 animate-spin mx-auto" />
        ) : (
          <span className="flex items-center gap-2 justify-center">
            {icon && <span className="w-4 h-4">{icon}</span>}
            {children}
          </span>
        )}
      </motion.button>
    );
  }
);

Button.displayName = 'Button';
