'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  Waves, 
  Radar, 
  Image as ImageIcon, 
  Activity, 
  FileText, 
  Info, 
  BookOpen,
  Cpu, 
  Database, 
  RefreshCw,
  ShieldCheck
} from 'lucide-react';

interface NavbarProps {
  surveyId?: string;
  qcStatus?: string;
  totalContacts?: number;
  onRefresh?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  surveyId,
  qcStatus,
  totalContacts,
  onRefresh
}) => {
  const pathname = usePathname();

  const navLinks = [
    { href: '/', label: 'Home', icon: Waves },
    { href: '/analyze', label: 'Analyze', icon: Radar },
    { href: '/samples', label: 'Sample Library', icon: ImageIcon },
    { href: '/model', label: 'Model & Performance', icon: Activity },
    { href: '/reports', label: 'Reports', icon: FileText },
    { href: '/about', label: 'About', icon: Info },
    { href: '/documentation', label: 'Documentation', icon: BookOpen },
  ];

  return (
    <header className="bg-ocean-900/95 backdrop-blur-md border-b border-ocean-700/60 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Logo & Title */}
          <Link href="/" className="flex items-center gap-3 group">
            <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-600 via-blue-600 to-indigo-600 shadow-lg shadow-cyan-500/25 group-hover:scale-105 transition-transform duration-200">
              <Waves className="w-5 h-5 text-white" />
              <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-emerald-400 rounded-full border-2 border-ocean-900 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-cyan-100 to-cyan-400 bg-clip-text text-transparent">
                  ABYSSEYE
                </span>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-cyan-950/90 text-cyan-300 border border-cyan-600/60 tracking-wider">
                  REAL PIPELINE
                </span>
              </div>
              <p className="text-[11px] text-slate-400 hidden sm:block">
                MoES • NIOT Sonar Evidence Engine
              </p>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden lg:flex items-center gap-1">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const isActive = pathname === link.href || (link.href !== '/' && pathname.startsWith(link.href));
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/40 shadow-sm shadow-cyan-500/10'
                      : 'text-slate-300 hover:text-white hover:bg-ocean-800/60'
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                  <span>{link.label}</span>
                </Link>
              );
            })}
          </nav>

          {/* Survey Telemetry / Actions */}
          <div className="flex items-center gap-3">
            {surveyId && (
              <div className="hidden xl:flex items-center gap-2 px-2.5 py-1 rounded-lg bg-ocean-800/80 border border-ocean-700/60 text-xs">
                <Database className="w-3.5 h-3.5 text-cyan-400" />
                <span className="text-slate-400 font-mono text-[11px]">{surveyId}</span>
              </div>
            )}

            {qcStatus && (
              <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-ocean-800/80 border border-ocean-700/60 text-xs">
                <Cpu className="w-3.5 h-3.5 text-blue-400" />
                <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${
                  qcStatus === 'EXCELLENT' ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-600/40' :
                  qcStatus === 'DEGRADED' ? 'bg-amber-950/80 text-amber-300 border border-amber-600/40' :
                  'bg-rose-950/80 text-rose-300 border border-rose-600/40'
                }`}>
                  {qcStatus}
                </span>
              </div>
            )}

            {totalContacts !== undefined && (
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-ocean-800/80 border border-ocean-700/60 text-xs">
                <ShieldCheck className="w-3.5 h-3.5 text-amber-400" />
                <span className="text-slate-400 hidden md:inline">Contacts:</span>
                <span className="font-bold text-amber-300 font-mono text-xs">
                  {totalContacts}
                </span>
              </div>
            )}

            {onRefresh && (
              <button
                onClick={onRefresh}
                title="Sync Pipeline State"
                className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-300 border border-cyan-500/40 text-xs font-medium transition active:scale-95"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Sync</span>
              </button>
            )}

            {/* Direct CTA */}
            <Link
              href="/analyze"
              className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white text-xs font-semibold shadow-md shadow-cyan-500/20 transition transform active:scale-95"
            >
              <Radar className="w-3.5 h-3.5" />
              <span>Live Analysis</span>
            </Link>
          </div>
        </div>

        {/* Mobile Navigation Row */}
        <div className="flex lg:hidden overflow-x-auto py-2 border-t border-ocean-800/60 gap-1 no-scrollbar">
          {navLinks.map((link) => {
            const Icon = link.icon;
            const isActive = pathname === link.href || (link.href !== '/' && pathname.startsWith(link.href));
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-medium whitespace-nowrap transition-all ${
                  isActive
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <Icon className="w-3 h-3" />
                <span>{link.label}</span>
              </Link>
            );
          })}
        </div>
      </div>
    </header>
  );
};
