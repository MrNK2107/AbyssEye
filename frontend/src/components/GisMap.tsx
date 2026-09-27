'use client';

import React from 'react';
import { ContactDigitalTwin } from '@/types/contact';
import { MapPin, Navigation, Compass, Radio } from 'lucide-react';

interface GisMapProps {
  contacts: ContactDigitalTwin[];
  selectedContactId: string | null;
  onSelectContact: (contact: ContactDigitalTwin) => void;
}

export const GisMap: React.FC<GisMapProps> = ({
  contacts,
  selectedContactId,
  onSelectContact
}) => {
  return (
    <div className="relative w-full h-full min-h-[460px] bg-ocean-950 rounded-2xl border border-ocean-700/80 overflow-hidden shadow-2xl flex flex-col">
      {/* Map Control Bar Overlay */}
      <div className="absolute top-3.5 left-3.5 z-10 flex items-center gap-2 bg-ocean-900/95 backdrop-blur px-3 py-1.5 rounded-xl border border-ocean-700/80 shadow-xl">
        <Navigation className="w-3.5 h-3.5 text-cyan-400" />
        <span className="text-xs font-mono font-bold text-slate-100">Bathymetric Survey GIS Swath</span>
        <span className="text-[10px] font-mono text-cyan-400 border-l border-ocean-700 pl-2">
          EPSG:4326 (WGS84)
        </span>
      </div>

      {/* Map Layer Legend Overlay */}
      <div className="absolute top-3.5 right-3.5 z-10 flex items-center gap-3 bg-ocean-900/95 backdrop-blur px-3 py-1.5 rounded-xl border border-ocean-700/80 text-[10px] font-mono font-bold shadow-xl">
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-rose-500 shadow-sm shadow-rose-500/50" />
          <span className="text-slate-200">Debris (&gt;80%)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-amber-400 shadow-sm shadow-amber-400/50" />
          <span className="text-slate-200">Review (40-80%)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400/50" />
          <span className="text-slate-200">Natural (&lt;40%)</span>
        </div>
      </div>

      {/* Interactive Bathymetric Grid & Contacts Overlay */}
      <div className="relative flex-1 w-full bg-[#050e1f] p-6 flex items-center justify-center overflow-hidden">
        {/* Bathymetric depth contour lines */}
        <svg className="absolute inset-0 w-full h-full opacity-35 pointer-events-none">
          <path d="M0,60 Q300,100 600,50 T1200,80" fill="none" stroke="#0284c7" strokeWidth="1.2" strokeDasharray="5 3" />
          <path d="M0,160 Q400,210 800,140 T1200,200" fill="none" stroke="#0ea5e9" strokeWidth="1.2" strokeDasharray="5 3" />
          <path d="M0,290 Q350,340 750,260 T1200,310" fill="none" stroke="#06b6d4" strokeWidth="1.2" strokeDasharray="5 3" />
          <path d="M0,420 Q500,470 900,390 T1200,430" fill="none" stroke="#14b8a6" strokeWidth="1.2" strokeDasharray="5 3" />
        </svg>

        {/* Sonar Swath Polygon & Trackline */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none">
          <polygon
            points="140,430 200,60 340,60 280,430"
            fill="rgba(6, 182, 212, 0.07)"
            stroke="rgba(6, 182, 212, 0.4)"
            strokeWidth="1"
            strokeDasharray="4 2"
          />
          <line x1="210" y1="430" x2="270" y2="60" stroke="#06b6d4" strokeWidth="2.5" />
        </svg>

        {/* Dynamic Contact Markers */}
        {contacts.length === 0 ? (
          <div className="flex flex-col items-center justify-center text-slate-500 font-mono text-xs z-10">
            <Radio className="w-8 h-8 mb-2 text-cyan-500/50 animate-pulse" />
            <span>Ready for Survey Stream — Click "Generate Survey" or Ingest Sonar Pings</span>
          </div>
        ) : (
          <div className="relative w-full h-full">
            {contacts.map((contact, idx) => {
              const isSelected = contact.contact_id === selectedContactId;
              const p_anth = contact.fusion_decision.calibrated_probabilities.p_anthropogenic;
              
              // Calculate spatial placement along simulated trackline
              const topOffset = 18 + ((idx * 17) % 65);
              const leftOffset = contact.channel === 'STARBOARD' ? (38 + ((idx * 11) % 40)) : (14 + ((idx * 9) % 22));

              const markerBg = p_anth > 0.80 ? 'bg-rose-500 text-white' : p_anth > 0.40 ? 'bg-amber-400 text-ocean-950' : 'bg-emerald-400 text-ocean-950';

              return (
                <button
                  key={contact.contact_id}
                  onClick={() => onSelectContact(contact)}
                  style={{ top: `${topOffset}%`, left: `${leftOffset}%` }}
                  className={`absolute transform -translate-x-1/2 -translate-y-1/2 group transition-all z-20 ${
                    isSelected ? 'scale-125 z-30' : 'hover:scale-110'
                  }`}
                >
                  {/* Radar Pulse for High-Risk Ghost Nets and Debris */}
                  {p_anth > 0.80 && (
                    <span className="absolute -inset-2.5 rounded-full bg-rose-500 opacity-40 animate-sonar pointer-events-none" />
                  )}

                  {/* Marker Pin */}
                  <div className={`flex items-center gap-1 px-2 py-0.5 rounded font-mono font-bold text-[11px] shadow-lg border-2 ${markerBg} ${
                    isSelected ? 'border-white ring-4 ring-cyan-400/60' : 'border-ocean-950'
                  }`}>
                    <MapPin className="w-3 h-3 fill-current" />
                    <span>{contact.contact_id.split('-').pop()}</span>
                  </div>

                  {/* Tooltip */}
                  <div className="opacity-0 group-hover:opacity-100 transition-opacity absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 p-2.5 rounded-xl bg-ocean-950/95 border border-ocean-700 text-left text-xs shadow-2xl pointer-events-none z-40 font-mono">
                    <div className="font-bold text-cyan-300 text-[11px]">{contact.contact_id}</div>
                    <div className="text-[10px] text-slate-300 font-semibold mt-1">
                      Type: <span className="text-yellow-400">{contact.target_type_hint.replace('_', ' ')}</span>
                    </div>
                    <div className="text-[10px] text-slate-400 mt-0.5">
                      P(Debris): <span className="text-rose-400 font-bold">{(p_anth * 100).toFixed(1)}%</span> • Ch: {contact.channel}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
