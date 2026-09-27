'use client';

import React from 'react';
import { Waves, ShieldAlert, Cpu, Database, RefreshCw, FileText } from 'lucide-react';

interface NavbarProps {
  surveyId: string;
  qcStatus: string;
  totalContacts: number;
  onRefresh: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  surveyId,
  qcStatus,
  totalContacts,
  onRefresh
}) => {
  return (
    <header className="bg-ocean-900/90 backdrop-blur border-b border-ocean-700/60 sticky top-0 z-50 px-6 py-3.5 flex items-center justify-between">
      {/* Brand & Logo */}
      <div className="flex items-center gap-3">
        <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-600 to-blue-500 shadow-lg shadow-cyan-500/20">
          <Waves className="w-6 h-6 text-white" />
          <span className="absolute -top-1 -right-1 w-3 h-3 bg-emerald-400 rounded-full border-2 border-ocean-900 animate-pulse" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-cyan-100 to-cyan-400 bg-clip-text text-transparent">
              ABYSSEYE
            </h1>
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-cyan-950/80 text-cyan-300 border border-cyan-700/50">
              SIH 26057 • v3.0
            </span>
          </div>
          <p className="text-xs text-slate-400">Autonomous Side-Scan Sonar Evidence & Ghost Net Detection Engine</p>
        </div>
      </div>

      {/* Active Survey Telemetry Badges */}
      <div className="flex items-center gap-4">
        {/* Survey Badge */}
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-ocean-800/80 border border-ocean-700/60 text-xs">
          <Database className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-slate-400">Survey:</span>
          <span className="font-mono font-medium text-slate-200">{surveyId}</span>
        </div>

        {/* QC Status Badge */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-ocean-800/80 border border-ocean-700/60 text-xs">
          <Cpu className="w-3.5 h-3.5 text-blue-400" />
          <span className="text-slate-400">Sensor QC:</span>
          <span className={`font-semibold px-1.5 py-0.5 rounded text-[11px] ${
            qcStatus === 'EXCELLENT' ? 'bg-emerald-950 text-emerald-300 border border-emerald-700/50' :
            qcStatus === 'DEGRADED' ? 'bg-amber-950 text-amber-300 border border-amber-700/50' :
            'bg-rose-950 text-rose-300 border border-rose-700/50'
          }`}>
            {qcStatus}
          </span>
        </div>

        {/* Contacts Count */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-ocean-800/80 border border-ocean-700/60 text-xs">
          <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
          <span className="text-slate-400">Surfaced Contacts:</span>
          <span className="font-bold text-amber-300 bg-amber-950/80 px-2 py-0.5 rounded border border-amber-800/50">
            {totalContacts}
          </span>
        </div>

        {/* Refresh Action */}
        <button
          onClick={onRefresh}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-300 border border-cyan-500/40 text-xs font-medium transition active:scale-95 shadow-sm"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Sync Pipeline</span>
        </button>
      </div>
    </header>
  );
};
