'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';
import { useOpenRouter } from '@/lib/openrouter-context';
import {
  LayoutDashboard,
  BarChart3,
  TrendingUp,
  Zap,
  Search,
  BookOpen,
  LineChart,
  FlaskConical,
  Settings,
  ChevronLeft,
  ChevronRight,
  Bot,
  Wifi,
  WifiOff,
} from 'lucide-react';

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/trading', label: 'Trading Workspace', icon: BarChart3 },
  { href: '/signals', label: 'Signal Center', icon: TrendingUp },
  { href: '/scanner', label: 'Scanner', icon: Search },
  { href: '/journal', label: 'Trade Journal', icon: BookOpen },
  { href: '/analytics', label: 'Analytics', icon: LineChart },
  { href: '/backtesting', label: 'Backtesting', icon: FlaskConical },
  { href: '/settings', label: 'Settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const { modelName, isConfigured, stats } = useOpenRouter();

  const displayModel = modelName.split('/').pop()?.replace(/-/g, ' ') || 'AI Model';

  return (
    <motion.aside
      initial={{ width: collapsed ? 72 : 260 }}
      animate={{ width: collapsed ? 72 : 260 }}
      transition={{ duration: 0.3, ease: 'easeInOut' }}
      className={cn(
        'fixed left-0 top-0 h-screen z-50',
        'glass border-r border-white/5',
        'flex flex-col'
      )}
    >
      <div className={cn('flex items-center gap-3 px-5 h-16 border-b border-white/5', collapsed && 'justify-center px-0')}>
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-aurora-400 to-cyber-500 flex items-center justify-center">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <AnimatePresence>
            {!collapsed && (
              <motion.div
                initial={{ opacity: 0, width: 0 }}
                animate={{ opacity: 1, width: 'auto' }}
                exit={{ opacity: 0, width: 0 }}
                className="overflow-hidden"
              >
                <span className="text-base font-bold bg-clip-text text-transparent bg-gradient-to-r from-aurora-400 to-cyber-400">
                  Scalpex
                </span>
                <span className="block text-[10px] font-medium text-[var(--color-text-muted)] tracking-widest uppercase">
                  AI
                </span>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto scrollbar-hide">
        {navItems.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
          const Icon = item.icon;

          return (
            <Link key={item.href} href={item.href}>
              <div
                className={cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group relative',
                  collapsed && 'justify-center px-2',
                  isActive
                    ? 'bg-aurora-500/10 text-aurora-400 border border-aurora-500/20'
                    : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)] hover:bg-white/[0.03] border border-transparent'
                )}
              >
                <Icon className="w-5 h-5 shrink-0" />
                <AnimatePresence>
                  {!collapsed && (
                    <motion.span
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -10 }}
                      className="text-sm font-medium whitespace-nowrap"
                    >
                      {item.label}
                    </motion.span>
                  )}
                </AnimatePresence>
                {isActive && !collapsed && (
                  <motion.div
                    layoutId="sidebar-active"
                    className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-6 bg-aurora-400 rounded-full"
                  />
                )}
              </div>
            </Link>
          );
        })}
      </nav>

      <div className="px-2 pb-4">
        <Link href="/settings">
          <div className={cn('glass-card p-3 border-aurora-500/10 cursor-pointer group transition-all hover:border-aurora-500/30', collapsed && 'p-2')}>
            {collapsed ? (
              <Bot className="w-5 h-5 text-aurora-400 mx-auto" />
            ) : (
              <div className="flex items-center gap-2">
                <div className="relative shrink-0">
                  <Bot className="w-4 h-4 text-aurora-400" />
                  {isConfigured && (
                    <span className="absolute -top-1 -right-1 w-2 h-2 bg-aurora-400 rounded-full animate-pulse" />
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-medium text-aurora-400 truncate group-hover:text-aurora-300 transition-colors">
                    {displayModel}
                  </p>
                  <div className="flex items-center gap-1 mt-0.5">
                    {isConfigured ? (
                      <>
                        <Wifi className="w-2.5 h-2.5 text-aurora-400" />
                        <span className="text-[9px] text-[var(--color-text-muted)]">
                          {stats ? `$${stats.totalCost.toFixed(4)}` : 'Connected'}
                        </span>
                      </>
                    ) : (
                      <>
                        <WifiOff className="w-2.5 h-2.5 text-ember-400" />
                        <span className="text-[9px] text-ember-400">Not configured</span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </Link>
      </div>

      <button
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center justify-center h-10 border-t border-white/5 text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
      >
        {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
      </button>
    </motion.aside>
  );
}
