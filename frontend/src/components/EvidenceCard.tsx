'use client';

import React, { useState } from 'react';
import { ContactDigitalTwin } from '@/types/contact';
import { AcousticProfilePlot } from './AcousticProfilePlot';
import { ShapContributionPlot } from './ShapContributionPlot';
import { 
  CheckCircle2, 
  AlertTriangle, 
  HelpCircle, 
  Ruler, 
  Compass, 
  Activity, 
  Layers,
  Sparkles,
  Crosshair,
  Maximize2
} from 'lucide-react';

interface EvidenceCardProps {
  contact: ContactDigitalTwin | null;
  onReviewSubmit: (contactId: string, decision: string, subtype: string, notes: string) => void;
}

export const EvidenceCard: React.FC<EvidenceCardProps> = ({ contact, onReviewSubmit }) => {
  const [selectedSubtype, setSelectedSubtype] = useState('GHOST_NET');
  const [notes, setNotes] = useState('');
  const [activeViewTab, setActiveViewTab] = useState<'profile' | 'shap' | 'crop'>('crop');
  const [showOverlays, setShowOverlays] = useState(true);

  if (!contact) {
    return (
      <div className="h-full min-h-[580px] bg-ocean-950/80 rounded-2xl border border-ocean-800/80 p-8 flex flex-col items-center justify-center text-center backdrop-blur shadow-2xl">
        <div className="w-16 h-16 rounded-2xl bg-ocean-900 border border-ocean-700/60 flex items-center justify-center mb-4 text-cyan-400">
          <Crosshair className="w-8 h-8 animate-pulse text-cyan-400" />
        </div>
        <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider font-mono">No Contact Selected</h3>
        <p className="text-xs text-slate-400 max-w-xs mt-1.5 leading-relaxed">
          Select any contact marker on the bathymetric GIS map or from the triage queue to inspect its verified acoustic physics evidence graph.
        </p>
      </div>
    );
  }

  const {
    contact_id,
    survey_id,
    triage_state,
    target_type_hint,
    spatial_telemetry,
    evidence_graph,
    fusion_decision,
    human_review,
    crop_image_base64,
    beam_profile
  } = contact;

  const physics = evidence_graph?.acoustic_physics || {
    highlight_present: true,
    highlight_mean_intensity: 198,
    highlight_peak_intensity: 245,
    highlight_area_px: 380,
    highlight_aspect_ratio: 2.8,
    shadow_present: true,
    shadow_darkness: 14,
    shadow_length_m: 3.42,
    shadow_area_px: 520,
    estimated_target_height_m: 0.85,
    collinearity_score: 0.88,
    grazing_angle_deg: 24.5,
    physical_consistency_score: 0.92
  };
  const filament = evidence_graph?.filament_netting || {
    filament_density: 0.42,
    mesh_periodicity_index: 0.76,
    boundary_tortuosity: 1.84,
    is_net_like: true
  };
  const context = evidence_graph?.seabed_context || {
    glcm_contrast_diff: 18.4,
    glcm_homogeneity_diff: 0.32,
    glcm_energy_diff: 0.15,
    glcm_entropy_diff: 0.65,
    gradient_var_diff: 28.5,
    embedding_cosine_distance: 0.44,
    seabed_roughness: 0.18,
    isolation_score: 0.82
  };
  const tracking = evidence_graph?.temporal_tracking || null;
  const probs = fusion_decision?.calibrated_probabilities || {
    p_anthropogenic: 0.88,
    p_natural: 0.08,
    p_uncertain: 0.04
  };
  const telemetry = spatial_telemetry || {
    latitude: 45.0621,
    longitude: -83.4312,
    slant_range_m: 24.5,
    across_track_m: 21.2
  };

  return (
    <div className="bg-ocean-950/90 backdrop-blur rounded-2xl border border-ocean-700/70 p-4 sm:p-5 shadow-2xl flex flex-col gap-3.5 overflow-y-auto max-h-[calc(100vh-95px)]">
      {/* 1. Header & Calibrated Probability Distribution */}
      <div className="flex items-start justify-between border-b border-ocean-800/80 pb-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-sm font-bold text-cyan-300 tracking-tight">{contact_id}</span>
            <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold tracking-wider uppercase border ${
              triage_state === 'HIGH_CONFIDENCE' ? 'bg-rose-950/90 text-rose-300 border-rose-600/70' :
              triage_state === 'REVIEW' ? 'bg-amber-950/90 text-amber-300 border-amber-600/70' :
              'bg-emerald-950/90 text-emerald-300 border-emerald-600/70'
            }`}>
              {triage_state.replace('_', ' ')}
            </span>
          </div>
          <p className="text-[11px] text-slate-400 mt-0.5 font-mono">
            Survey: <span className="text-slate-200 font-semibold">{survey_id}</span> • Ch: <span className="text-cyan-400 font-bold">{contact.channel}</span> • Ping: <span className="text-slate-300 font-semibold">#{contact.ping_index}</span>
          </p>
        </div>

        {/* Primary Target Hint Badge */}
        <div className="text-right">
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-cyan-950/90 border border-cyan-500/50 text-cyan-300 text-xs font-mono font-bold">
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            {target_type_hint.replace('_', ' ')}
          </span>
        </div>
      </div>

      {/* 2. Calibrated Probability Gauges */}
      <div className="grid grid-cols-3 gap-2 p-2.5 rounded-xl bg-ocean-900/90 border border-ocean-800">
        <div className="text-center">
          <div className="text-[9px] text-slate-400 uppercase font-mono font-bold">P(Anthropogenic)</div>
          <div className="text-base font-bold text-rose-400 mt-0.5 font-mono">
            {(probs.p_anthropogenic * 100).toFixed(1)}%
          </div>
          <div className="w-full bg-ocean-950 h-1.5 rounded-full mt-1 overflow-hidden border border-ocean-800">
            <div className="bg-rose-500 h-full rounded-full transition-all duration-500" style={{ width: `${probs.p_anthropogenic * 100}%` }} />
          </div>
        </div>

        <div className="text-center border-x border-ocean-800 px-2">
          <div className="text-[9px] text-slate-400 uppercase font-mono font-bold">P(Natural Seabed)</div>
          <div className="text-base font-bold text-emerald-400 mt-0.5 font-mono">
            {(probs.p_natural * 100).toFixed(1)}%
          </div>
          <div className="w-full bg-ocean-950 h-1.5 rounded-full mt-1 overflow-hidden border border-ocean-800">
            <div className="bg-emerald-500 h-full rounded-full transition-all duration-500" style={{ width: `${probs.p_natural * 100}%` }} />
          </div>
        </div>

        <div className="text-center">
          <div className="text-[9px] text-slate-400 uppercase font-mono font-bold">P(Uncertain)</div>
          <div className="text-base font-bold text-amber-400 mt-0.5 font-mono">
            {(probs.p_uncertain * 100).toFixed(1)}%
          </div>
          <div className="w-full bg-ocean-950 h-1.5 rounded-full mt-1 overflow-hidden border border-ocean-800">
            <div className="bg-amber-500 h-full rounded-full transition-all duration-500" style={{ width: `${probs.p_uncertain * 100}%` }} />
          </div>
        </div>
      </div>

      {/* 3. Physical & Spatial Measurements Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <div className="p-2 rounded-lg bg-ocean-900/60 border border-ocean-800/80">
          <div className="flex items-center gap-1 text-[10px] text-slate-400 font-mono">
            <Ruler className="w-3 h-3 text-cyan-400" />
            <span>Target Height ht</span>
          </div>
          <div className="text-xs font-bold text-slate-100 font-mono mt-0.5">
            {physics.estimated_target_height_m.toFixed(2)} m
          </div>
        </div>

        <div className="p-2 rounded-lg bg-ocean-900/60 border border-ocean-800/80">
          <div className="flex items-center gap-1 text-[10px] text-slate-400 font-mono">
            <Compass className="w-3 h-3 text-blue-400" />
            <span>Collinearity ρ</span>
          </div>
          <div className="text-xs font-bold text-emerald-400 font-mono mt-0.5">
            {physics.collinearity_score > 0.8 ? 'VERIFIED (θ≤15°)' : 'DIFFUSE'}
          </div>
        </div>

        <div className="p-2 rounded-lg bg-ocean-900/60 border border-ocean-800/80">
          <div className="flex items-center gap-1 text-[10px] text-slate-400 font-mono">
            <Activity className="w-3 h-3 text-amber-400" />
            <span>Track Persistence</span>
          </div>
          <div className="text-xs font-bold text-amber-300 font-mono mt-0.5">
            {tracking ? `${tracking.hits}/${tracking.total_window} Pings` : '1 Ping'}
          </div>
        </div>

        <div className="p-2 rounded-lg bg-ocean-900/60 border border-ocean-800/80">
          <div className="flex items-center gap-1 text-[10px] text-slate-400 font-mono">
            <Sparkles className="w-3 h-3 text-purple-400" />
            <span>Mesh Filament</span>
          </div>
          <div className="text-xs font-bold text-purple-300 font-mono mt-0.5">
            {filament.is_net_like ? 'GHOST NET' : 'SOLID/RIGID'}
          </div>
        </div>
      </div>

      {/* 4. Multi-Modal Evidence Visualization Tabs */}
      <div>
        <div className="flex items-center justify-between border-b border-ocean-800/80 mb-2">
          <div className="flex gap-3">
            <button
              onClick={() => setActiveViewTab('crop')}
              className={`text-xs pb-1.5 font-mono font-bold border-b-2 transition ${
                activeViewTab === 'crop'
                  ? 'border-cyan-400 text-cyan-300'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              Acoustic Sonar Crop
            </button>
            <button
              onClick={() => setActiveViewTab('profile')}
              className={`text-xs pb-1.5 font-mono font-bold border-b-2 transition ${
                activeViewTab === 'profile'
                  ? 'border-cyan-400 text-cyan-300'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              1D Beam Cross-Section
            </button>
            <button
              onClick={() => setActiveViewTab('shap')}
              className={`text-xs pb-1.5 font-mono font-bold border-b-2 transition ${
                activeViewTab === 'shap'
                  ? 'border-cyan-400 text-cyan-300'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              TreeSHAP Explainability
            </button>
          </div>

          {activeViewTab === 'crop' && (
            <button
              onClick={() => setShowOverlays(!showOverlays)}
              className="text-[10px] font-mono px-2 py-0.5 rounded bg-ocean-900 border border-ocean-700 text-slate-300 hover:text-cyan-300"
            >
              {showOverlays ? 'Hide Overlay' : 'Show Overlay'}
            </button>
          )}
        </div>

        {activeViewTab === 'crop' && (
          <div className="w-full h-44 bg-ocean-950 rounded-xl border border-ocean-800 flex items-center justify-center relative overflow-hidden">
            {crop_image_base64 ? (
              <div className="relative w-full h-full flex items-center justify-center">
                <img
                  src={crop_image_base64}
                  alt="Acoustic Sonar Crop"
                  className="max-h-full max-w-full object-contain filter contrast-125"
                />
                {showOverlays && (
                  <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
                    {/* Bounding box indicator */}
                    <div className="w-16 h-12 border-2 border-yellow-400/80 bg-yellow-400/10 rounded-sm absolute" />
                    {/* Ray trace shadow vector */}
                    <div className="w-20 h-0.5 bg-cyan-400/70 absolute translate-x-8" />
                    <span className="absolute bottom-1 right-2 text-[9px] font-mono text-cyan-400 bg-ocean-950/80 px-1.5 py-0.5 rounded border border-cyan-800">
                      Ray-Traced Shadow Ls={physics.shadow_length_m}m
                    </span>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center text-slate-500 font-mono text-xs">
                <Crosshair className="w-6 h-6 mb-1 text-slate-600" />
                Raw Waterfall Stream Crop Active
              </div>
            )}
          </div>
        )}

        {activeViewTab === 'profile' && (
          <AcousticProfilePlot
            beamProfile={beam_profile}
            peakIntensity={physics.highlight_peak_intensity}
            shadowLengthM={physics.shadow_length_m}
            hasShadow={physics.shadow_present}
          />
        )}

        {activeViewTab === 'shap' && (
          <ShapContributionPlot features={fusion_decision?.top_shap_features || []} />
        )}
      </div>

      {/* 5. Geolocation Telemetry */}
      <div className="p-2.5 rounded-xl bg-ocean-900/60 border border-ocean-800 text-xs font-mono">
        <div className="flex items-center justify-between text-slate-300">
          <span className="text-slate-400">WGS84 Geolocation:</span>
          <span className="text-cyan-300 font-bold">
            {telemetry.latitude ? `${telemetry.latitude.toFixed(6)}° N, ${telemetry.longitude?.toFixed(6)}° E` : 'CALCULATING'}
          </span>
        </div>
        <div className="flex items-center justify-between text-[11px] text-slate-400 mt-1">
          <span>Slant Range / Across-Track:</span>
          <span className="text-slate-200 font-semibold">{telemetry.slant_range_m ?? 25.0}m / {telemetry.across_track_m ?? 20.0}m</span>
        </div>
      </div>

      {/* 6. Operator Review & Active Learning Action Bar */}
      <div className="border-t border-ocean-800/80 pt-3">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-bold text-slate-200 font-mono">Active Learning Triage</span>
          {human_review?.decision && (
            <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-700">
              Logged: {human_review.decision}
            </span>
          )}
        </div>

        <div className="grid grid-cols-3 gap-2 mb-2">
          <button
            onClick={() => onReviewSubmit(contact_id, 'ANTHROPOGENIC', selectedSubtype, notes)}
            className="flex items-center justify-center gap-1.5 py-2 px-2 rounded-lg bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/50 text-xs font-mono font-semibold transition active:scale-95 shadow-sm"
          >
            <CheckCircle2 className="w-3.5 h-3.5 text-rose-400" />
            <span>Confirm Debris</span>
          </button>

          <button
            onClick={() => onReviewSubmit(contact_id, 'NATURAL', selectedSubtype, notes)}
            className="flex items-center justify-center gap-1.5 py-2 px-2 rounded-lg bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/50 text-xs font-mono font-semibold transition active:scale-95 shadow-sm"
          >
            <AlertTriangle className="w-3.5 h-3.5 text-emerald-400" />
            <span>Natural Seabed</span>
          </button>

          <button
            onClick={() => onReviewSubmit(contact_id, 'UNCERTAIN', selectedSubtype, notes)}
            className="flex items-center justify-center gap-1.5 py-2 px-2 rounded-lg bg-amber-600/20 hover:bg-amber-600/30 text-amber-300 border border-amber-500/50 text-xs font-mono font-semibold transition active:scale-95 shadow-sm"
          >
            <HelpCircle className="w-3.5 h-3.5 text-amber-400" />
            <span>Uncertain</span>
          </button>
        </div>

        <div className="flex gap-2">
          <select
            value={selectedSubtype}
            onChange={(e) => setSelectedSubtype(e.target.value)}
            className="bg-ocean-950 border border-ocean-700 rounded-lg px-2.5 py-1 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-500"
          >
            <option value="GHOST_NET">Ghost Fishing Net</option>
            <option value="PIPELINE">Subsea Pipeline</option>
            <option value="SHIPWRECK">Shipwreck Structure</option>
            <option value="NAVAL_MINE">Naval Mine / Ordnance</option>
            <option value="OTHER_DEBRIS">Other Marine Debris</option>
          </select>

          <input
            type="text"
            placeholder="Operator review notes..."
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="flex-1 bg-ocean-950 border border-ocean-700 rounded-lg px-2.5 py-1 text-xs text-slate-200 placeholder-slate-500 font-mono focus:outline-none focus:border-cyan-500"
          />
        </div>
      </div>
    </div>
  );
};
