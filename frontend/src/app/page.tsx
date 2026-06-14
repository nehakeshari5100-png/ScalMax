'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { motion, useScroll, useTransform } from 'framer-motion';
import { ArrowRight, Zap, Brain, TrendingUp, Shield, BarChart3, Search, BookOpen, FlaskConical, LineChart, ChevronDown, Star, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { GlassCard, GlassPanel } from '@/components/ui/GlassCard';
import { cn } from '@/lib/utils';

const fadeInUp = {
  initial: { opacity: 0, y: 30 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true },
  transition: { duration: 0.6, ease: 'easeOut' },
};

const stagger = {
  initial: { opacity: 0 },
  whileInView: { opacity: 1 },
  viewport: { once: true },
  transition: { staggerChildren: 0.1 },
};

const features = [
  { icon: BarChart3, title: 'Trading Workspace', desc: 'Professional-grade charting with ICT concepts, order blocks, FVG, and liquidity zones overlaid in real-time.', color: 'aurora' },
  { icon: TrendingUp, title: 'Signal Engine', desc: 'Multi-engine confluence scoring (math-based) + AI analyst overlay. No signal relies solely on AI.', color: 'amber' },
  { icon: Brain, title: 'AI Analyst', desc: 'OpenRouter-powered analysis with hot-swappable models. AI reads charts and provides structured trade insights.', color: 'blue' },
  { icon: Shield, title: 'Risk Engine', desc: 'Kelly, volatility-adjusted, and fixed-ratio position sizing. ATR-based and structure-based SL/TP.', color: 'green' },
  { icon: Search, title: 'Market Scanner', desc: 'Real-time multi-symbol scanning. Detects OB, FVG, liquidity sweeps, CHoCH across all timeframes.', color: 'purple' },
  { icon: BookOpen, title: 'Trade Journal', desc: 'Auto-logging with screenshots, tags, performance analytics. Searchable trade history with metrics.', color: 'pink' },
];

const metrics = [
  { value: '98.5%', label: 'Uptime' },
  { value: '<50ms', label: 'Latency' },
  { value: '24/7', label: 'Monitoring' },
  { value: '8', label: 'Exchanges' },
];

const testimonials = [
  { quote: 'Scalpex changed how I trade. The confluence scoring is incredibly accurate.', name: 'Alex K.', role: 'Crypto Trader, 5yr' },
  { quote: 'The ICT engine alone is worth it. It catches order blocks I would miss.', name: 'Sarah M.', role: 'Full-time Trader' },
  { quote: 'Finally, a platform that uses AI as a tool, not a crutch. Pure math + AI = winning.', name: 'Marcus J.', role: 'Prop Firm Trader' },
];

export default function LandingPage() {
  const { scrollYProgress } = useScroll();
  const opacity = useTransform(scrollYProgress, [0, 0.15], [1, 0]);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouse = (e: MouseEvent) => {
      setMousePos({ x: e.clientX, y: e.clientY });
    };
    window.addEventListener('mousemove', handleMouse);
    return () => window.removeEventListener('mousemove', handleMouse);
  }, []);

  return (
    <div className="min-h-screen bg-[var(--color-bg)] overflow-hidden">
      {/* Floating background gradient */}
      <div
        className="fixed pointer-events-none w-[600px] h-[600px] rounded-full opacity-[0.03] blur-[120px]"
        style={{
          background: 'radial-gradient(circle, #00c48c, #0040ff)',
          left: mousePos.x - 300,
          top: mousePos.y - 300,
          transition: 'left 0.3s, top 0.3s',
        }}
      />

      {/* Grid overlay */}
      <div className="fixed inset-0 pointer-events-none grid-lines opacity-30" />

      {/* Nav */}
      <nav className="relative z-50 flex items-center justify-between px-6 lg:px-12 h-20 border-b border-white/5 glass/50">
        <div className="flex items-center gap-2">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-aurora-400 to-cyber-500 flex items-center justify-center">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <span className="text-lg font-bold">
            <span className="text-gradient">Scalpex</span>
            <span className="text-xs text-[var(--color-text-muted)] ml-1 font-mono">AI</span>
          </span>
        </div>
        <div className="hidden md:flex items-center gap-8">
          {['Features', 'Engine', 'Pricing', 'Docs'].map(item => (
            <a key={item} href={`#${item.toLowerCase()}`} className="text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text)] transition-colors">
              {item}
            </a>
          ))}
        </div>
        <div className="flex items-center gap-3">
          <Link href="/dashboard">
            <Button variant="ghost" size="sm">Sign In</Button>
          </Link>
          <Link href="/dashboard">
            <Button variant="primary" size="sm">
              Get Started
              <ArrowRight className="w-3.5 h-3.5" />
            </Button>
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative px-6 lg:px-12 pt-20 lg:pt-32 pb-20 text-center">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          className="max-w-4xl mx-auto"
        >
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-aurora-500/10 border border-aurora-500/20 text-aurora-400 text-xs font-medium mb-8">
            <Sparkles className="w-3.5 h-3.5" />
            Next-Gen Crypto Scalping Platform
          </div>

          <h1 className="text-4xl lg:text-7xl font-bold leading-tight mb-6">
            Trade Smarter with{' '}
            <span className="text-gradient">AI-Powered</span>
            <br />
            Scalping Intelligence
          </h1>

          <p className="text-lg text-[var(--color-text-secondary)] max-w-2xl mx-auto mb-10 leading-relaxed">
            The most advanced crypto scalping platform. 
            <strong className="text-[var(--color-text)]"> Pure math engines</strong> for indicators, structure, and liquidity —
            <strong className="text-[var(--color-text)]"> AI as your professional analyst</strong>.
            No signal relies on AI alone.
          </p>

          <div className="flex items-center justify-center gap-4">
            <Link href="/dashboard">
              <Button variant="primary" size="lg" icon={<Zap className="w-4 h-4" />}>
                Launch Dashboard
              </Button>
            </Link>
            <Button variant="outline" size="lg">
              Watch Demo
            </Button>
          </div>
        </motion.div>

        {/* Hero Image */}
        <motion.div
          initial={{ opacity: 0, y: 60 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.3, ease: 'easeOut' }}
          className="mt-16 max-w-6xl mx-auto relative"
        >
          <div className="glass rounded-2xl p-2 border border-white/10 shadow-glow">
            <div className="rounded-xl bg-surface-dark/80 p-4 flex items-center gap-3 border-b border-white/5">
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-red-500" />
                <div className="w-3 h-3 rounded-full bg-ember-400" />
                <div className="w-3 h-3 rounded-full bg-aurora-400" />
              </div>
              <div className="flex-1 flex items-center gap-3 text-xs text-[var(--color-text-muted)] font-mono">
                <span className="text-aurora-400">scalpex</span>
                <span>~/dashboard</span>
                <span className="flex-1" />
                <span className="flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-aurora-400 animate-pulse" />
                  Live
                </span>
              </div>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-4 gap-4 mb-4">
                {['BTC', 'ETH', 'SOL', 'AVAX'].map((sym, i) => (
                  <div key={sym} className="glass-card p-3 flex items-center justify-between">
                    <span className="text-xs font-semibold">{sym}</span>
                    <span className={cn('text-xs font-mono', i % 2 === 0 ? 'text-aurora-400' : 'text-red-400')}>
                      {i % 2 === 0 ? '+' : ''}{[2.34, -1.23, 5.67, -0.89][i]}%
                    </span>
                  </div>
                ))}
              </div>
              <div className="h-48 rounded-lg bg-gradient-to-r from-aurora-500/5 via-cyber-500/5 to-aurora-500/5 border border-white/5 flex items-center justify-center">
                <div className="text-center">
                  <BarChart3 className="w-8 h-8 text-aurora-400/50 mx-auto mb-2" />
                  <p className="text-xs text-[var(--color-text-muted)]">Live Chart with ICT Concepts</p>
                </div>
              </div>
            </div>
          </div>

          {/* Glow behind hero */}
          <div className="absolute -bottom-20 left-1/2 -translate-x-1/2 w-[400px] h-[200px] bg-aurora-500/10 blur-[100px] rounded-full" />
        </motion.div>
      </section>

      {/* Features */}
      <section id="features" className="px-6 lg:px-12 py-24">
        <motion.div {...fadeInUp} className="text-center mb-16">
          <h2 className="text-3xl lg:text-5xl font-bold mb-4">
            Everything You Need to{' '}
            <span className="text-gradient">Scale</span>
          </h2>
          <p className="text-[var(--color-text-secondary)] max-w-2xl mx-auto">
            8 integrated engines working in unison. Every calculation is mathematically precise.
            AI provides professional analysis, not trading decisions.
          </p>
        </motion.div>

        <motion.div {...stagger} className="grid md:grid-cols-2 lg:grid-cols-3 gap-5 max-w-6xl mx-auto">
          {features.map((feature, i) => {
            const Icon = feature.icon;
            return (
              <motion.div key={feature.title} {...fadeInUp} transition={{ delay: i * 0.1 }}>
                <GlassCard className="h-full group" glow="green">
                  <div className={cn(
                    'w-10 h-10 rounded-lg flex items-center justify-center mb-4 transition-all duration-300 group-hover:scale-110',
                    `bg-${feature.color}-500/10`
                  )}>
                    <Icon className={`w-5 h-5 text-${feature.color}-400`} />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                  <p className="text-sm text-[var(--color-text-secondary)] leading-relaxed">{feature.desc}</p>
                </GlassCard>
              </motion.div>
            );
          })}
        </motion.div>
      </section>

      {/* Engine Architecture */}
      <section id="engine" className="px-6 lg:px-12 py-24 relative">
        <div className="max-w-6xl mx-auto">
          <motion.div {...fadeInUp} className="text-center mb-16">
            <h2 className="text-3xl lg:text-5xl font-bold mb-4">
              Pure Math +{' '}
              <span className="text-gradient">AI Analyst</span>
            </h2>
            <p className="text-[var(--color-text-secondary)] max-w-2xl mx-auto">
              Our architecture ensures no signal relies on AI alone. Every engine runs on pure mathematics.
            </p>
          </motion.div>

          <div className="grid lg:grid-cols-3 gap-6">
            <GlassPanel className="border-aurora-500/20" glow="green">
              <h3 className="text-sm font-semibold text-aurora-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                <Zap className="w-4 h-4" /> Math Engines
              </h3>
              <div className="space-y-3">
                {['Indicator Engine (numpy/pandas_ta)', 'Market Structure Engine (algorithmic)', 'Liquidity Engine (order book math)', 'Confluence Engine (weighted scoring)'].map(item => (
                  <div key={item} className="flex items-center gap-2 text-sm text-[var(--color-text-secondary)]">
                    <div className="w-1.5 h-1.5 rounded-full bg-aurora-400 shrink-0" />
                    {item}
                  </div>
                ))}
              </div>
            </GlassPanel>

            <GlassPanel className="border-cyber-500/20 relative" glow="blue">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 rounded-full bg-cyber-500/20 border border-cyber-500/30 text-xs text-cyber-400 font-medium">
                AI Layer
              </div>
              <h3 className="text-sm font-semibold text-cyber-400 uppercase tracking-wider mb-4 flex items-center gap-2 mt-2">
                <Brain className="w-4 h-4" /> Gemma Vision Engine
              </h3>
              <div className="space-y-3">
                {['OpenRouter — hot-swappable models', 'Chart screenshot analysis', 'Structured insight extraction', 'Confidence scoring overlay'].map(item => (
                  <div key={item} className="flex items-center gap-2 text-sm text-[var(--color-text-secondary)]">
                    <div className="w-1.5 h-1.5 rounded-full bg-cyber-400 shrink-0" />
                    {item}
                  </div>
                ))}
              </div>
            </GlassPanel>

            <GlassPanel className="border-ember-500/20" glow="amber">
              <h3 className="text-sm font-semibold text-ember-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                <Shield className="w-4 h-4" /> Execution Layer
              </h3>
              <div className="space-y-3">
                {['Risk Engine (Kelly, volatility-adjusted)', 'Signal Engine (dedup, priority, cooldown)', 'Exchange Execution (manual/auto toggle)', 'Trade Journal (auto-logging + analytics)'].map(item => (
                  <div key={item} className="flex items-center gap-2 text-sm text-[var(--color-text-secondary)]">
                    <div className="w-1.5 h-1.5 rounded-full bg-ember-400 shrink-0" />
                    {item}
                  </div>
                ))}
              </div>
            </GlassPanel>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="px-6 lg:px-12 py-16">
        <div className="max-w-4xl mx-auto">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
            {metrics.map((metric, i) => (
              <motion.div
                key={metric.label}
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="text-center"
              >
                <div className="text-3xl lg:text-4xl font-bold text-gradient mb-1">{metric.value}</div>
                <div className="text-sm text-[var(--color-text-muted)]">{metric.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="px-6 lg:px-12 py-24">
        <motion.div {...fadeInUp} className="max-w-6xl mx-auto">
          <h2 className="text-3xl lg:text-5xl font-bold text-center mb-12">
            Trusted by{' '}
            <span className="text-gradient">Professional Traders</span>
          </h2>
          <div className="grid md:grid-cols-3 gap-6">
            {testimonials.map((t, i) => (
              <motion.div key={i} {...fadeInUp} transition={{ delay: i * 0.1 }}>
                <GlassCard className="h-full">
                  <div className="flex gap-1 mb-4">
                    {Array.from({ length: 5 }).map((_, j) => (
                      <Star key={j} className="w-4 h-4 fill-ember-400 text-ember-400" />
                    ))}
                  </div>
                  <p className="text-sm text-[var(--color-text-secondary)] leading-relaxed mb-4">"{t.quote}"</p>
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-aurora-400 to-cyber-500 flex items-center justify-center text-xs font-bold">
                      {t.name.charAt(0)}
                    </div>
                    <div>
                      <p className="text-sm font-medium">{t.name}</p>
                      <p className="text-xs text-[var(--color-text-muted)]">{t.role}</p>
                    </div>
                  </div>
                </GlassCard>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </section>

      {/* CTA */}
      <section className="px-6 lg:px-12 py-24">
        <motion.div {...fadeInUp} className="max-w-3xl mx-auto text-center">
          <GlassPanel className="border-aurora-500/20" glow="green">
            <h2 className="text-3xl lg:text-5xl font-bold mb-4">
              Ready to{' '}
              <span className="text-gradient">Scale</span> Your Trading?
            </h2>
            <p className="text-[var(--color-text-secondary)] mb-8 max-w-xl mx-auto">
              Join professional traders using Scalpex AI. Set up in 2 minutes — just add your OpenRouter key.
            </p>
            <Link href="/dashboard">
              <Button variant="primary" size="lg" icon={<Zap className="w-4 h-4" />}>
                Launch Scalpex AI
              </Button>
            </Link>
          </GlassPanel>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="px-6 lg:px-12 py-8 border-t border-white/5">
        <div className="max-w-6xl mx-auto flex items-center justify-between text-sm text-[var(--color-text-muted)]">
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-aurora-400" />
            <span>Scalpex AI</span>
          </div>
          <div className="flex items-center gap-6">
            <span>Docs</span>
            <span>API</span>
            <span>Terms</span>
            <span className="text-xs">&copy; 2026 Scalpex AI</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
