'use client';

import { ReactNode } from 'react';
import { usePathname } from 'next/navigation';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Inter } from 'next/font/google';
import '@/styles/globals.css';
import { Sidebar } from '@/components/layout/Sidebar';
import { Header } from '@/components/layout/Header';
import { LiveTicker } from '@/components/widgets/LiveTicker';
import { OpenRouterProvider } from '@/lib/openrouter-context';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: false,
    },
  },
});

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

function AppLayout({ children }: { children: ReactNode }) {
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

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} font-sans`}>
        <QueryClientProvider client={queryClient}>
          <OpenRouterProvider>
            <AppLayout>{children}</AppLayout>
          </OpenRouterProvider>
        </QueryClientProvider>
      </body>
    </html>
  );
}
