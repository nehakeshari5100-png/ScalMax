'use client';

import { ReactNode } from 'react';
import { usePathname } from 'next/navigation';
import { Sidebar } from '@/components/layout/Sidebar';
import { Header } from '@/components/layout/Header';
import { LiveTicker } from '@/components/widgets/LiveTicker';

const APP_PAGES = ['/dashboard', '/trading', '/signals', '/scanner', '/journal', '/analytics', '/backtesting', '/settings'];

const pageTitles: Record<string, { title: string; subtitle: string }> = {
  '/dashboard': { title: 'Dashboard', subtitle: 'Real-time portfolio overview' },
  '/trading': { title: 'Trading Workspace', subtitle: 'Advanced charting and trade execution' },
  '/signals': { title: 'Signal Center', subtitle: 'AI-powered trading signals' },
  '/scanner': { title: 'Market Scanner', subtitle: 'Multi-timeframe pattern detection' },
  '/journal': { title: 'Trade Journal', subtitle: 'Trade history and performance' },
  '/analytics': { title: 'Analytics', subtitle: 'Performance metrics and insights' },
  '/backtesting': { title: 'Backtesting', subtitle: 'Strategy optimization and simulation' },
  '/settings': { title: 'Settings', subtitle: 'Configure Scalpex AI' },
};

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const isApp = APP_PAGES.includes(pathname);
  const pageInfo = pageTitles[pathname] || { title: 'Scalpex AI', subtitle: '' };

  if (!isApp) {
    return <>{children}</>;
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col ml-[260px] transition-all duration-300">
        <LiveTicker />
        <Header title={pageInfo.title} subtitle={pageInfo.subtitle} />
        <div className="flex-1 overflow-y-auto bg-[var(--color-bg)]">
          {children}
        </div>
      </div>
    </div>
  );
}
