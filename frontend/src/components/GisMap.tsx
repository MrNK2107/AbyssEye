'use client';

import React, { useState } from 'react';
import { Navigation, Compass, Target, Waves, Layers, ZoomIn, ZoomOut, RotateCcw, AlertTriangle, ShieldCheck } from 'lucide-react';
import { ContactDigitalTwin } from '@/types/contact';

interface GisMapProps {
  contacts: ContactDigitalTwin[];
  selectedContactId: string | null;
  onSelectContact: (contact: ContactDigitalTwin) => void;
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
    latitude: 45.0621,
    longitude: -83.4312,
    heading_deg: 135.0,
    altitude_m: 12.0,
    depth_m: 34.5,
    speed_knots: 3.0
  },
  missionTitle = "Thunder Bay AUV Sanctuary Mission",
  region = "Lake Huron • NOAA Thunder Bay NMS"
}) => {
  const [filterDebrisOnly, setFilterDebrisOnly] = useState(true);
  const [hoveredContact, setHoveredContact] = useState<ContactDigitalTwin | null>(null);

  // Filter contacts to avoid visual clutter
  const displayContacts = contacts.filter((c) => {
    const pAnth = c.fusion_decision?.calibrated_probabilities?.p_anthropogenic ?? (c as any).confidence ?? 0.85;
    const isNatural = (c.triage_state || '').includes('NATURAL') && pAnth < 0.35;
    if (filterDebrisOnly) {
      return !isNatural || c.contact_id === selectedContactId;
    }
    return true;
  }).slice(0, 30); // Max 30 relevant targets on map

  const debrisCount = contacts.filter(c => {
    const p = c.fusion_decision?.calibrated_probabilities?.p_anthropogenic ?? (c as any).confidence ?? 0.85;
    return p >= 0.50 || c.triage_state === 'HIGH_CONFIDENCE';
  }).length;

  return (
    <div className="relative w-full h-full min-h-[390px] bg-slate-950 rounded-xl border border-slate-800 overflow-hidden shadow-2xl flex flex-col backdrop-blur-md">
      {/* Top Header Overlay */}
      <div className="flex flex-wrap items-center justify-between px-4 py-2.5 bg-slate-950/90 border-b border-slate-800/80 z-20 gap-2">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
            <Compass className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xs font-semibold text-slate-200 tracking-wide">{missionTitle}</div>
            <div className="text-[10px] font-mono text-slate-400">{region} • EPSG:4326</div>
          </div>
        </div>

        {/* Live Navigation & Map Filters */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setFilterDebrisOnly(!filterDebrisOnly)}
            className={`px-2 py-1 rounded text-[10px] font-mono font-bold flex items-center gap-1.5 border transition ${
              filterDebrisOnly
                ? 'bg-rose-500/20 border-rose-500/40 text-rose-300'
                : 'bg-slate-900 border-slate-750 text-slate-400 hover:text-slate-200'
            }`}
            title="Toggle between All Anomalies vs Confirmed Targets"
          >
            <Target className="w-3 h-3" />
            <span>{filterDebrisOnly ? 'Debris Targets' : 'All Detections'} ({debrisCount})</span>
          </button>

          <div className="hidden sm:flex items-center gap-2 font-mono text-[11px] bg-slate-900/90 px-2.5 py-1 rounded-lg border border-slate-800 text-slate-300">
            <span className="text-cyan-400 font-semibold">
              {auvTelemetry.latitude.toFixed(4)}°N, {Math.abs(auvTelemetry.longitude).toFixed(4)}°W
            </span>
            <span className="text-slate-700">|</span>
            <span className="text-amber-400 font-semibold">{auvTelemetry.heading_deg.toFixed(0)}°</span>
          </div>
        </div>
      </div>

      {/* GIS Canvas & Bathymetric Chart */}
      <div className="relative flex-1 w-full bg-[#030712] flex items-center justify-center overflow-hidden select-none min-h-[300px]">
        {/* Bathymetric Grid & Depth Contours */}
        <svg className="absolute inset-0 w-full h-full opacity-25 pointer-events-none">
          <defs>
            <pattern id="gis-grid" width="48" height="48" patternUnits="userSpaceOnUse">
              <path d="M 48 0 L 0 0 0 48" fill="none" stroke="#1e293b" strokeWidth="0.75" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#gis-grid)" />
          
          {/* Depth Contours (10m, 25m, 40m, 60m) */}
          <path d="M-50,60 Q200,120 500,40 T1100,80" fill="none" stroke="#0ea5e9" strokeWidth="1.2" strokeDasharray="6 4" />
          <path d="M-50,150 Q300,210 650,130 T1100,190" fill="none" stroke="#06b6d4" strokeWidth="1.2" strokeDasharray="6 4" />
          <path d="M-50,250 Q250,320 600,230 T1100,280" fill="none" stroke="#14b8a6" strokeWidth="1.2" strokeDasharray="6 4" />
          <path d="M-50,330 Q400,390 750,310 T1100,360" fill="none" stroke="#3b82f6" strokeWidth="1.2" strokeDasharray="6 4" />
        </svg>

        {/* Survey Trackline Path (Simulated Lawnmower AUV Survey) */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-40">
          <polyline
            points="80,240 180,120 280,240 380,120 480,240 580,120 680,240"
            fill="none"
            stroke="#06b6d4"
            strokeWidth="2"
            strokeDasharray="4 4"
          />
        </svg>

        {/* Dynamic AUV Vehicle & Swath Fan */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div
            style={{ transform: `rotate(${auvTelemetry.heading_deg}deg)` }}
            className="relative w-44 h-56 transition-transform duration-500 flex flex-col items-center justify-center"
          >
            {/* Swath Beam Projection Cone */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-36 h-48 bg-gradient-to-t from-cyan-500/15 via-cyan-500/5 to-transparent clip-path-fan border-t border-cyan-400/40 rounded-t-full shadow-[0_0_20px_rgba(6,182,212,0.15)]" />
            
            {/* AUV Vehicle Icon */}
            <div className="relative z-30 flex items-center justify-center w-8 h-8 rounded-full bg-slate-900 border-2 border-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.9)]">
              <Navigation className="w-4 h-4 text-cyan-300" />
            </div>

            {/* Sonar Acoustic Pulse Ping */}
            <div className="absolute w-12 h-12 rounded-full border border-cyan-400/50 animate-ping pointer-events-none" />
          </div>
        </div>

        {/* Interactive Sonar Contact Radar Blips */}
        <div className="relative w-full h-full">
          {displayContacts.map((contact, idx) => {
            const isSelected = contact.contact_id === selectedContactId;
            const pAnth = contact.fusion_decision?.calibrated_probabilities?.p_anthropogenic ?? (contact as any).confidence ?? 0.85;
            const isDebris = pAnth > 0.65 || contact.triage_state === 'HIGH_CONFIDENCE';
            const isReview = !isDebris && (pAnth > 0.30 || contact.triage_state === 'REVIEW');
            
            // Clean deterministic spatial scatter across the survey corridor
            const channelOffset = contact.channel === 'STARBOARD' ? 14 : -14;
            const basePos = ((idx * 37 + 11) % 76);
            const posX = Math.max(12, Math.min(88, 50 + channelOffset + ((idx % 2 === 0 ? 1 : -1) * (basePos / 3.5))));
            const posY = Math.max(15, Math.min(82, 18 + ((idx * 17) % 64)));

            const targetName = (contact.target_type_hint || (contact as any).classification || (isDebris ? 'GHOST NET' : 'ANOMALY')).replace(/_/g, ' ');

            return (
              <div
                key={contact.contact_id || idx}
                style={{ top: `${posY}%`, left: `${posX}%` }}
                className={`absolute transform -translate-x-1/2 -translate-y-1/2 z-20 ${
                  isSelected ? 'z-40 scale-125' : 'hover:scale-110 z-30'
                }`}
              >
                {/* Pulsing Target Aura */}
                {isDebris && (
                  <span className="absolute -inset-2 rounded-full bg-rose-500/50 animate-ping pointer-events-none" />
                )}

                {/* Radar Blip Button */}
                <button
                  onClick={() => onSelectContact(contact)}
                  onMouseEnter={() => setHoveredContact(contact)}
                  onMouseLeave={() => setHoveredContact(null)}
                  className={`relative flex items-center justify-center w-6 h-6 rounded-full transition-all shadow-lg border ${
                    isSelected
                      ? 'bg-cyan-400 border-white text-slate-950 shadow-[0_0_15px_rgba(6,182,212,1)] ring-2 ring-cyan-300'
                      : isDebris
                        ? 'bg-rose-600/90 border-rose-300 text-white shadow-[0_0_10px_rgba(244,63,94,0.6)] hover:bg-rose-500'
                        : isReview
                          ? 'bg-amber-600/90 border-amber-300 text-slate-950 shadow-[0_0_8px_rgba(245,158,11,0.5)] hover:bg-amber-500'
                          : 'bg-slate-800 border-slate-600 text-slate-400'
                  }`}
                  title={`${contact.contact_id} (${(pAnth * 100).toFixed(0)}%)`}
                >
                  <span className="text-[9px] font-mono font-bold">
                    {idx + 1}
                  </span>
                </button>

                {/* Hover Tooltip Card */}
                {(hoveredContact?.contact_id === contact.contact_id || isSelected) && (
                  <div className="absolute left-1/2 -translate-x-1/2 bottom-8 w-44 p-2 rounded-lg bg-slate-950/95 border border-slate-700 shadow-2xl backdrop-blur-md pointer-events-none z-50 text-left">
                    <div className="flex items-center justify-between text-[10px] font-mono font-bold">
                      <span className={isDebris ? 'text-rose-400' : 'text-amber-400'}>
                        {targetName}
                      </span>
                      <span className="text-slate-300">
                        {(pAnth * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="text-[9px] font-mono text-slate-400 mt-0.5 truncate">
                      {contact.contact_id}
                    </div>
                    <div className="flex items-center justify-between text-[9px] font-mono text-slate-500 mt-1 border-t border-slate-800 pt-1">
                      <span>Ch: <strong className="text-cyan-400">{contact.channel || 'STBD'}</strong></span>
                      <span>Slant: <strong className="text-slate-300">{contact.spatial_telemetry?.slant_range_m ?? 24}m</strong></span>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* GIS Footer Status & Legend */}
        <div className="absolute bottom-2.5 left-3 flex items-center gap-3 px-2.5 py-1 rounded-md bg-slate-950/85 border border-slate-800 text-[10px] font-mono backdrop-blur-sm">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-rose-500 shadow-[0_0_5px_rgba(244,63,94,0.8)]" />
            <span className="text-slate-300">Confirmed Debris</span>
          </div>
          <span className="text-slate-700">•</span>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-amber-500 shadow-[0_0_5px_rgba(245,158,11,0.8)]" />
            <span className="text-slate-400">Review</span>
          </div>
        </div>

        {/* Map Bottom-Right Telemetry */}
        <div className="absolute bottom-2.5 right-3 flex items-center gap-2 px-2.5 py-1 rounded-md bg-slate-950/85 border border-slate-800 text-[10px] font-mono text-slate-400 backdrop-blur-sm">
          <Waves className="w-3.5 h-3.5 text-cyan-400" />
          <span>Depth: <strong className="text-slate-200">{auvTelemetry.depth_m.toFixed(1)}m</strong></span>
          <span className="text-slate-700">|</span>
          <span>Speed: <strong className="text-slate-200">{auvTelemetry.speed_knots.toFixed(1)} kts</strong></span>
        </div>
      </div>
    </div>
  );
};
