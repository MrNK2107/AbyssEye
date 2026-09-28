'use client';

import React from 'react';
import { Navigation, Compass, Radio, Target, Waves } from 'lucide-react';

interface GisMapProps {
  contacts: any[];
  selectedContactId: string | null;
  onSelectContact: (contact: any) => void;
  auvTelemetry?: {
    latitude: number;
    longitude: number;
    heading_deg: number;
    altitude_m: number;
    depth_m: number;
    speed_knots: number;
  };
  missionTitle?: string;
  region?: string;
}

export const GisMap: React.FC<GisMapProps> = ({
  contacts,
  selectedContactId,
  onSelectContact,
  auvTelemetry = {
    latitude: 55.3214,
    longitude: 14.8920,
    heading_deg: 45.0,
    altitude_m: 11.5,
    depth_m: 48.5,
    speed_knots: 3.0
  },
  missionTitle = "Baltic Sea Debris Patrol",
  region = "Bornholm Basin"
}) => {
  return (
    <div className="relative w-full h-full min-h-[380px] bg-slate-950 rounded-xl border border-slate-800 overflow-hidden shadow-2xl flex flex-col backdrop-blur-md">
      {/* Top Header Overlay */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-slate-900/90 border-b border-slate-800/80 z-10">
        <div className="flex items-center gap-2">
          <div className="p-1 rounded bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
            <Compass className="w-3.5 h-3.5" />
          </div>
          <div>
            <div className="text-xs font-semibold text-slate-200">{missionTitle}</div>
            <div className="text-[10px] font-mono text-slate-400">{region} • EPSG:4326 (WGS84)</div>
          </div>
        </div>

        {/* Live Coordinate Pill */}
        <div className="flex items-center gap-3 font-mono text-[11px] bg-slate-950/80 px-2.5 py-1 rounded-lg border border-slate-800">
          <span className="text-cyan-400">
            {auvTelemetry.latitude.toFixed(4)}°N, {auvTelemetry.longitude.toFixed(4)}°E
          </span>
          <span className="text-slate-600">|</span>
          <span className="text-amber-400">HDG: {auvTelemetry.heading_deg.toFixed(0)}°</span>
          <span className="text-slate-600">|</span>
          <span className="text-emerald-400">ALT: {auvTelemetry.altitude_m.toFixed(1)}m</span>
        </div>
      </div>

      {/* GIS Canvas & Vector Map Area */}
      <div className="relative flex-1 w-full bg-[#040913] flex items-center justify-center overflow-hidden select-none">
        {/* Bathymetric Depth Contours */}
        <svg className="absolute inset-0 w-full h-full opacity-20 pointer-events-none">
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" strokeWidth="0.8" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
          <path d="M-100,80 Q300,140 700,60 T1400,100" fill="none" stroke="#0ea5e9" strokeWidth="1.5" strokeDasharray="6 4" />
          <path d="M-100,180 Q400,240 850,160 T1400,220" fill="none" stroke="#06b6d4" strokeWidth="1.5" strokeDasharray="6 4" />
          <path d="M-100,310 Q350,380 800,290 T1400,340" fill="none" stroke="#14b8a6" strokeWidth="1.5" strokeDasharray="6 4" />
        </svg>

        {/* Dynamic AUV Trackline & Swath Cone */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          {/* Swath Beam Projection */}
          <div
            style={{ transform: `rotate(${auvTelemetry.heading_deg}deg)` }}
            className="relative w-48 h-64 transition-transform duration-300 flex flex-col items-center justify-center"
          >
            {/* Projected Sonar Fan */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-40 h-52 bg-gradient-to-t from-cyan-500/10 via-cyan-500/5 to-transparent clip-path-fan border-t border-cyan-500/30 rounded-t-full" />
            
            {/* AUV Vehicle Icon */}
            <div className="relative z-20 flex items-center justify-center w-8 h-8 rounded-full bg-cyan-500/20 border-2 border-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.8)]">
              <Navigation className="w-4 h-4 text-cyan-300" />
            </div>

            {/* Vessel Pulsing Ring */}
            <div className="absolute w-12 h-12 rounded-full border border-cyan-400/40 animate-ping" />
          </div>
        </div>

        {/* Contact Pins Overlay */}
        <div className="relative w-full h-full">
          {contacts.map((contact, idx) => {
            const isSelected = contact.contact_id === selectedContactId;
            const pAnth = contact.fusion_decision?.calibrated_probabilities?.p_anthropogenic ?? (contact.confidence || 0.85);
            const isDebris = pAnth > 0.75;

            // Distribution along GIS screen coordinates
            const posX = 15 + ((idx * 23 + (contact.channel === 'STARBOARD' ? 35 : 0)) % 70);
            const posY = 20 + ((idx * 19) % 60);

            return (
              <button
                key={contact.contact_id || idx}
                onClick={() => onSelectContact(contact)}
                style={{ top: `${posY}%`, left: `${posX}%` }}
                className={`absolute transform -translate-x-1/2 -translate-y-1/2 group transition-all z-20 ${
                  isSelected ? 'scale-125 z-30' : 'hover:scale-110'
                }`}
              >
                {isDebris && (
                  <span className="absolute -inset-2 rounded-full bg-rose-500/40 animate-ping pointer-events-none" />
                )}
                <div
                  className={`flex items-center gap-1 px-2 py-0.5 rounded-md font-mono text-[10px] font-bold shadow-lg border ${
                    isSelected
                      ? 'bg-cyan-500 text-slate-950 border-white shadow-cyan-500/50'
                      : isDebris
                        ? 'bg-rose-500/90 text-white border-rose-400 shadow-rose-500/30'
                        : 'bg-amber-500/90 text-slate-950 border-amber-300 shadow-amber-500/30'
                  }`}
                >
                  <Target className="w-3 h-3" />
                  <span>{((contact.classification || contact.target_type_hint || 'ANOMALY') as string).replace(/_/g, ' ').slice(0, 12)}</span>
                  <span>{(pAnth * 100).toFixed(0)}%</span>
                </div>
              </button>
            );
          })}
        </div>

        {/* Map Corner Scale */}
        <div className="absolute bottom-2 right-3 flex items-center gap-2 px-2 py-1 rounded bg-slate-950/80 border border-slate-800 text-[10px] font-mono text-slate-400">
          <Waves className="w-3 h-3 text-cyan-400" />
          <span>Depth: <strong>{auvTelemetry.depth_m.toFixed(1)}m</strong></span>
          <span className="text-slate-600">|</span>
          <span>Speed: <strong>{auvTelemetry.speed_knots.toFixed(1)} kts</strong></span>
        </div>
      </div>
    </div>
  );
};
