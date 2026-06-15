'use client';

import { ReactNode } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Zap, BarChart3, Settings } from 'lucide-react';
import { cn } from '@/lib/utils';

const NAV_ITEMS = [
  { href: '/analysis', label: 'Analysis', icon: BarChart3 },
  { href: '/settings', label: 'Settings', icon: Settings },
];

const AUTH_PAGES = ['/login'];
const NO_NAV_PAGES = [...AUTH_PAGES, '/'];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  if (NO_NAV_PAGES.includes(pathname)) return <>{children}</>;

  return (
    <div className="flex flex-col min-h-screen bg-[var(--color-bg)]">
      <nav className="sticky top-0 z-50 flex items-center justify-between px-4 lg:px-8 h-14 border-b border-white/5 bg-[var(--color-bg)]/90 backdrop-blur-md">
        <Link href="/analysis" className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-md bg-gradient-to-br from-aurora-400 to-cyber-500 flex items-center justify-center">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <span className="text-sm font-bold">
            <span className="text-gradient">Scalpex</span>
          </span>
        </Link>
        <div className="flex items-center gap-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors',
                  isActive ? 'text-aurora-400 bg-aurora-500/10' : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text)] hover:bg-white/5',
                )}
              >
                <Icon className="w-3.5 h-3.5" />
                {item.label}
              </Link>
            );
          })}
        </div>
      </nav>
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
  );
}
