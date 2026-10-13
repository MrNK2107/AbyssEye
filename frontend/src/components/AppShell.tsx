'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  House,
  Play,
  Library,
  ChartNoAxesColumn,
  FileText,
  CircleHelp,
  BookOpen,
  Waves,
  Activity,
} from 'lucide-react';

const NAV_LINKS = [
  { to: '/', label: 'Home', icon: House },
  { to: '/analyze', label: 'Analyze', icon: Play },
  { to: '/samples', label: 'Sample Library', icon: Library },
  { to: '/model', label: 'Model & Performance', icon: ChartNoAxesColumn },
  { to: '/reports', label: 'Reports', icon: FileText },
  { to: '/about', label: 'About', icon: CircleHelp },
  { to: '/documentation', label: 'Documentation', icon: BookOpen },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link
          href="/"
          className={`brand ${pathname === '/' ? 'active' : ''}`}
          data-status={pathname === '/' ? 'active' : undefined}
          aria-current={pathname === '/' ? 'page' : undefined}
        >
          <Waves className="brand-mark" strokeWidth={2.6} />
          <div>
            <strong>ABYSSEYE</strong>
            <small>Underwater Sonar Intelligence</small>
          </div>
        </Link>

        <nav className="nav-group" aria-label="Main navigation">
          {NAV_LINKS.map(({ to, label, icon: Icon }) => {
            const isActive = pathname === to;
            return (
              <Link
                key={to}
                href={to}
                className={`nav-link ${isActive ? 'active' : ''}`}
                data-status={isActive ? 'active' : undefined}
                aria-current={isActive ? 'page' : undefined}
              >
                <Icon strokeWidth={1.8} size={17} />
                {label}
              </Link>
            );
          })}
        </nav>

        <div className="sidebar-foot">
          <Waves size={30} strokeWidth={2} />
          <strong>
            Cleaner Oceans
            <br />
            Safer Futures
          </strong>
          <p>AI-powered insight for underwater detection and analysis.</p>
        </div>
      </aside>

      <div className="main-area">
        <header className="topbar">
          <div className="topbar-left">
            <Activity size={15} />
            SONAR INTELLIGENCE PLATFORM <span className="muted">/</span> PROTOTYPE
          </div>
          <div className="topbar-right">
            <span className="status-dot"></span>
            LIVE PIPELINE <span>·</span> REAL VALUES
          </div>
        </header>

        <main className="content">{children}</main>
      </div>
    </div>
  );
}
