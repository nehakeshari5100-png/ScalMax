'use client';

import { useState } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';
import { useOpenRouter } from '@/lib/openrouter-context';
import {
  Bell,
  Search,
  ChevronDown,
  Wifi,
  WifiOff,
  Settings,
  LogOut,
  User,
  Bot,
  Brain,
  Activity,
  DollarSign,
} from 'lucide-react';
import { Badge } from '@/components/ui/Badge';

interface HeaderProps {
  title: string;
  subtitle?: string;
  connected?: boolean;
}

export function Header({ title, subtitle, connected = true }: HeaderProps) {
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const { modelName, isConfigured, stats } = useOpenRouter();

  const displayModel = modelName.split('/').pop()?.replace(/-/g, ' ') || 'AI Model';

  const notifications = [
    { id: 1, text: 'SOL/USDT signal confidence upgraded to 91', time: '2m ago', type: 'signal' },
    { id: 2, text: 'BTC/USDT took TP1 at 68200', time: '15m ago', type: 'trade' },
    { id: 3, text: 'Daily P&L target reached: +$420.50', time: '1h ago', type: 'alert' },
    { id: 4, text: 'AVAX/USDT stop loss hit at 35.80', time: '3h ago', type: 'risk' },
  ];

  return (
    <header className="h-16 glass border-b border-white/5 flex items-center justify-between px-6 sticky top-0 z-40">
      <div className="flex items-center gap-4">
        <div>
          <h1 className="text-lg font-semibold">{title}</h1>
          {subtitle && (
            <p className="text-xs text-[var(--color-text-muted)]">{subtitle}</p>
          )}
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Model Badge */}
        <Link href="/settings">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-dark/60 border border-white/5 hover:border-aurora-500/20 transition-colors cursor-pointer group">
            <Brain className="w-3.5 h-3.5 text-cyber-400 group-hover:text-cyber-300 transition-colors" />
            <span className="text-xs font-medium text-[var(--color-text-secondary)] group-hover:text-[var(--color-text)] transition-colors hidden sm:inline">
              {displayModel}
            </span>
            {isConfigured ? (
              <Wifi className="w-3 h-3 text-aurora-400" />
            ) : (
              <WifiOff className="w-3 h-3 text-ember-400" />
            )}
          </div>
        </Link>

        {/* Cost Indicator */}
        {stats && stats.totalRequests > 0 && (
          <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-surface-dark/40 border border-white/5">
            <DollarSign className="w-3 h-3 text-aurora-400" />
            <span className="text-[11px] font-mono text-[var(--color-text-secondary)]">
              ${stats.totalCost.toFixed(5)}
            </span>
          </div>
        )}

        {/* Connection Status */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-dark/60 border border-white/5">
          {connected ? (
            <Wifi className="w-3.5 h-3.5 text-aurora-400" />
          ) : (
            <WifiOff className="w-3.5 h-3.5 text-red-400" />
          )}
          <span className={cn('text-xs font-medium', connected ? 'text-aurora-400' : 'text-red-400')}>
            {connected ? 'Live' : 'Offline'}
          </span>
        </div>

        {/* Notifications */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="relative p-2 rounded-lg hover:bg-white/[0.05] transition-colors"
          >
            <Bell className="w-5 h-5 text-[var(--color-text-secondary)]" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-aurora-400 rounded-full animate-pulse" />
          </button>

          <AnimatePresence>
            {showNotifications && (
              <motion.div
                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 10, scale: 0.95 }}
                className="absolute right-0 top-full mt-2 w-80 glass rounded-xl border border-white/5 shadow-glass p-2"
              >
                <div className="flex items-center justify-between px-3 py-2 border-b border-white/5">
                  <span className="text-sm font-medium">Notifications</span>
                  <span className="text-xs text-aurora-400 cursor-pointer">Mark all read</span>
                </div>
                <div className="space-y-1 mt-1">
                  {notifications.map(n => (
                    <div key={n.id} className="px-3 py-2 rounded-lg hover:bg-white/[0.03] cursor-pointer transition-colors">
                      <p className="text-sm">{n.text}</p>
                      <p className="text-xs text-[var(--color-text-muted)] mt-0.5">{n.time}</p>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* User Menu */}
        <div className="relative">
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center gap-2 p-1.5 rounded-lg hover:bg-white/[0.05] transition-colors"
          >
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-aurora-500 to-cyber-600 flex items-center justify-center">
              <User className="w-4 h-4 text-white" />
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-[var(--color-text-muted)] hidden sm:block" />
          </button>

          <AnimatePresence>
            {showUserMenu && (
              <motion.div
                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 10, scale: 0.95 }}
                className="absolute right-0 top-full mt-2 w-52 glass rounded-xl border border-white/5 shadow-glass p-1.5"
              >
                <div className="px-3 py-2 border-b border-white/5 mb-1">
                  <p className="text-xs font-medium">Scalpex Operator</p>
                  <p className="text-[10px] text-[var(--color-text-muted)]">{displayModel}</p>
                </div>
                {[
                  { icon: Activity, label: 'AI Analytics', href: '/analytics' },
                  { icon: Bot, label: 'Model Settings', href: '/settings' },
                  { icon: Settings, label: 'Settings', href: '/settings' },
                  { icon: LogOut, label: 'Sign Out', href: '#' },
                ].map(item => (
                  <Link
                    key={item.label}
                    href={item.href}
                    className="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text)] hover:bg-white/[0.05] transition-colors"
                    onClick={() => setShowUserMenu(false)}
                  >
                    <item.icon className="w-4 h-4" />
                    {item.label}
                  </Link>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </header>
  );
}
