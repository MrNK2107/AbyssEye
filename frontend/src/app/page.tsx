'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Navbar } from '@/components/Navbar';
import { GisMap } from '@/components/GisMap';
import { EvidenceCard } from '@/components/EvidenceCard';
import { TriageQueue } from '@/components/TriageQueue';
import { LiveWaterfallViewer } from '@/components/LiveWaterfallViewer';
import { ContactDigitalTwin } from '@/types/contact';
import { 
  Play, 
  Pause, 
  SkipForward, 
  Upload, 
  Radio, 
  Compass, 
  Gauge, 
  Activity, 
  Layers, 
  ShieldCheck, 
  Download,
  RefreshCw,
  FolderArchive,
  ChevronRight
} from 'lucide-react';

const API_BASE = 'http://localhost:8000/api/v1';
const WS_URL = 'ws://localhost:8000/api/v1/ws/live-stream';

interface MissionSummary {
  key: string;
  mission_id: string;
  title: string;
  region: string;
  environment: string;
  origin_coords: [number, number];
  nominal_depth_m: number;
  nominal_altitude_m: number;
  speed_knots: number;
  total_pings: number;
  is_active: boolean;
}

export default function MissionDashboard() {
  const [missions, setMissions] = useState<MissionSummary[]>([]);
  const [activeMissionKey, setActiveMissionKey] = useState<string>('baltic_debris');
  const [contacts, setContacts] = useState<ContactDigitalTwin[]>([]);
  const [selectedContact, setSelectedContact] = useState<ContactDigitalTwin | null>(null);
  
  // Real-time Simulation State
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1.0);
  const [currentPingIndex, setCurrentPingIndex] = useState<number>(0);
  const [totalPings, setTotalPings] = useState<number>(40);
  const [frameImage, setFrameImage] = useState<string | undefined>(undefined);
  const [frameWidth, setFrameWidth] = useState<number>(768);
  const [frameHeight, setFrameHeight] = useState<number>(384);
  
  // Telemetry & QC
  const [telemetry, setTelemetry] = useState({
    latitude: 55.3214,
    longitude: 14.8920,
    heading_deg: 45.0,
    altitude_m: 11.5,
    depth_m: 48.5,
    speed_knots: 3.0,
    slant_range_m: 50.0,
    frequency_khz: 900.0
  });
  const [qcStatus, setQcStatus] = useState<string>('PASS');
  const [snrDb, setSnrDb] = useState<number>(24.2);
  const [wsConnected, setWsConnected] = useState<boolean>(false);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [showUploadModal, setShowUploadModal] = useState<boolean>(false);

  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const playbackTimerRef = useRef<NodeJS.Timeout | null>(null);

  // 1. Fetch available missions and initial contacts
  const fetchMissions = async () => {
    try {
      const res = await fetch(`${API_BASE}/sonar/missions`);
      if (res.ok) {
        const data = await res.json();
        setMissions(data.missions || []);
        if (data.active_mission) {
          setActiveMissionKey(data.active_mission);
        }
      }
    } catch (err) {
      console.error('Failed to fetch missions:', err);
    }
  };

  const fetchContacts = async () => {
    try {
      const res = await fetch(`${API_BASE}/contacts`);
      if (res.ok) {
        const data: ContactDigitalTwin[] = await res.json();
        setContacts(data);
        if (data.length > 0 && !selectedContact) {
          setSelectedContact(data[0]);
        }
      }
    } catch (err) {
      console.error('Failed to fetch contacts:', err);
    }
  };

  useEffect(() => {
    fetchMissions();
    fetchContacts();
    // Fetch initial ping frame
    stepMissionPing();
  }, []);

  // 2. Select Mission
  const handleSelectMission = async (key: string) => {
    try {
      const res = await fetch(`${API_BASE}/sonar/missions/select`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mission_key: key })
      });
      if (res.ok) {
        const data = await res.json();
        setActiveMissionKey(key);
        setCurrentPingIndex(0);
        if (data.initial_payload) {
          applyPingPayload(data.initial_payload);
        }
      }
    } catch (err) {
      console.error('Failed to select mission:', err);
    }
  };

  // 3. Step Single Ping
  const stepMissionPing = async () => {
    try {
      const res = await fetch(`${API_BASE}/sonar/missions/step`, {
        method: 'POST'
      });
      if (res.ok) {
        const data = await res.json();
        if (data.payload) {
          applyPingPayload(data.payload);
        }
      }
    } catch (err) {
      console.error('Failed to step mission ping:', err);
    }
  };

  // 4. Apply Incoming Ping Data
  const applyPingPayload = (payload: any) => {
    setCurrentPingIndex(payload.ping_index + 1);
    setTotalPings(payload.total_pings || 40);
    if (payload.frame_image) setFrameImage(payload.frame_image);
    if (payload.frame_width) setFrameWidth(payload.frame_width);
    if (payload.frame_height) setFrameHeight(payload.frame_height);
    if (payload.telemetry) setTelemetry(payload.telemetry);
    if (payload.qc_report) {
      setQcStatus(payload.qc_report.overall_pass ? 'PASS' : 'WARN');
      setSnrDb(payload.qc_report.snr_db || 20.0);
    }

    if (payload.contacts && payload.contacts.length > 0) {
      setContacts((prev) => {
        const existingIds = new Set(prev.map((c) => c.contact_id));
        const newContacts = payload.contacts.filter((c: any) => !existingIds.has(c.contact_id));
        const updated = [...newContacts, ...prev];
        if (!selectedContact && updated.length > 0) {
          setSelectedContact(updated[0]);
        }
        return updated;
      });
    }
  };

  // 5. Playback Timer Controller
  useEffect(() => {
    if (isPlaying) {
      const intervalMs = Math.max(200, 1000 / playbackSpeed);
      playbackTimerRef.current = setInterval(() => {
        stepMissionPing();
      }, intervalMs);
    } else {
      if (playbackTimerRef.current) {
        clearInterval(playbackTimerRef.current);
      }
    }
    return () => {
      if (playbackTimerRef.current) clearInterval(playbackTimerRef.current);
    };
  }, [isPlaying, playbackSpeed]);

  // 6. Handle Custom ZIP Survey Upload
  const handleZipUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('survey_title', file.name.replace(/\.[^/.]+$/, ''));

    try {
      const res = await fetch(`${API_BASE}/sonar/upload-zip-stream`, {
        method: 'POST',
        body: formData
      });

      if (res.ok) {
        const data = await res.json();
        await fetchMissions();
        setActiveMissionKey(data.mission_key);
        if (data.initial_payload) {
          applyPingPayload(data.initial_payload);
        }
        setShowUploadModal(false);
      } else {
        const errData = await res.json();
        alert(`Upload error: ${errData.detail || 'Failed to process ZIP file'}`);
      }
    } catch (err) {
      console.error('Upload failed:', err);
      alert('Network error during survey ZIP upload.');
    } finally {
      setIsUploading(false);
    }
  };

  // 7. Active Mission Details
  const currentMission = missions.find((m) => m.key === activeMissionKey) || {
    key: 'baltic_debris',
    mission_id: 'MSN-BALTIC-SWDD-01',
    title: 'Baltic Sea Debris & Ordnance Patrol',
    region: 'Bornholm Basin',
    environment: 'Historic Munitions Zone',
    nominal_depth_m: 48.5,
    nominal_altitude_m: 11.5,
    origin_coords: [55.3214, 14.8920] as [number, number],
    speed_knots: 3.0,
    total_pings: 40,
    is_active: true
  };

  // 8. Handle Review Submission
  const handleReviewSubmit = async (contactId: string, decision: string, subtype: string, notes: string) => {
    try {
      const res = await fetch(`${API_BASE}/contacts/${contactId}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decision, subtype, notes })
      });
      if (res.ok) {
        const updated = await res.json();
        setContacts((prev) =>
          prev.map((c) => (c.contact_id === contactId ? { ...c, ...updated, triage_state: decision } : c))
        );
        if (selectedContact?.contact_id === contactId) {
          setSelectedContact((prev) => prev ? { ...prev, ...updated, triage_state: decision } : null);
        }
      }
    } catch (err) {
      console.error('Failed to submit review:', err);
    }
  };

  return (
    <div className="min-h-screen bg-[#030712] text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-black">
      <Navbar
        surveyId={currentMission.mission_id || 'MSN-BALTIC-SWDD-01'}
        qcStatus={qcStatus}
        totalContacts={contacts.length}
        onRefresh={() => {
          fetchMissions();
          fetchContacts();
        }}
      />

      {/* Main Ground Station Container */}
      <main className="flex-1 max-w-[1780px] w-full mx-auto p-3 sm:p-5 flex flex-col gap-4">
        {/* Mission Control & Telemetry Bar                                          */}
        {/* ========================================================================= */}
        <section className="bg-slate-900/90 border border-slate-800/90 rounded-2xl p-3.5 shadow-2xl backdrop-blur-md flex flex-wrap items-center justify-between gap-4">
          {/* Left: Mission Selector Dropdown */}
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
              <Compass className="w-5 h-5" />
            </div>
            <div>
              <div className="text-[10px] font-mono text-slate-400 uppercase tracking-widest">Active Survey Mission</div>
              <select
                value={activeMissionKey}
                onChange={(e) => handleSelectMission(e.target.value)}
                className="bg-slate-950 border border-slate-700/80 rounded-lg px-2.5 py-1 text-xs font-semibold text-slate-100 focus:outline-none focus:border-cyan-400 cursor-pointer"
              >
                {missions.map((m) => (
                  <option key={m.key} value={m.key}>
                    {m.title} ({m.region})
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Center: Live Playback Controls */}
          <div className="flex items-center gap-2.5 bg-slate-950/80 border border-slate-800 rounded-xl px-3 py-1.5 shadow-inner">
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-bold transition shadow ${
                isPlaying 
                  ? 'bg-amber-500 text-slate-950 hover:bg-amber-400' 
                  : 'bg-cyan-500 text-slate-950 hover:bg-cyan-400'
              }`}
            >
              {isPlaying ? <Pause className="w-3.5 h-3.5 fill-current" /> : <Play className="w-3.5 h-3.5 fill-current" />}
              <span>{isPlaying ? 'PAUSE' : 'STREAM'}</span>
            </button>

            <button
              onClick={stepMissionPing}
              disabled={isPlaying}
              className="p-1.5 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 disabled:opacity-40"
              title="Step Next Ping"
            >
              <SkipForward className="w-3.5 h-3.5" />
            </button>

            {/* Speed Multiplier */}
            <div className="flex items-center gap-1 ml-2 text-[11px] font-mono">
              {[0.5, 1.0, 2.0, 5.0].map((spd) => (
                <button
                  key={spd}
                  onClick={() => setPlaybackSpeed(spd)}
                  className={`px-1.5 py-0.5 rounded ${playbackSpeed === spd ? 'bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-500/40' : 'text-slate-400 hover:text-slate-200'}`}
                >
                  {spd}x
                </button>
              ))}
            </div>

            {/* Ping Progress Counter */}
            <div className="ml-3 pl-3 border-l border-slate-800 font-mono text-xs text-slate-300">
              Ping <strong className="text-cyan-400">{currentPingIndex}</strong> / {totalPings}
            </div>
          </div>

          {/* Right: Upload SSS ZIP & Telemetry Status */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowUploadModal(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 border border-slate-700 text-slate-200 hover:bg-slate-700 hover:border-slate-600 text-xs font-medium transition shadow"
            >
              <Upload className="w-3.5 h-3.5 text-cyan-400" />
              <span>Upload Sonar ZIP</span>
            </button>

            <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono">
              <span className="flex h-2 w-2 relative">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
              </span>
              <span className="text-emerald-400 font-semibold">QC: {qcStatus}</span>
              <span className="text-slate-500">|</span>
              <span className="text-slate-300">{snrDb.toFixed(1)} dB</span>
            </div>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* Top Grid: Live Sonar Waterfall + Bathymetric GIS Map                     */}
        {/* ========================================================================= */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          {/* Left Column (7 cols): Dual-Channel Acoustic Waterfall */}
          <div className="lg:col-span-7 flex flex-col">
            <LiveWaterfallViewer
              frameImage={frameImage}
              frameWidth={frameWidth}
              frameHeight={frameHeight}
              contacts={contacts as any}
              selectedContactId={selectedContact?.contact_id}
              onSelectContact={(c: any) => setSelectedContact(c)}
              slantRangeM={telemetry.slant_range_m}
              frequencyKhz={telemetry.frequency_khz}
              snrDb={snrDb}
            />
          </div>

          {/* Right Column (5 cols): Bathymetric GIS Map */}
          <div className="lg:col-span-5 flex flex-col">
            <GisMap
              contacts={contacts}
              selectedContactId={selectedContact?.contact_id || null}
              onSelectContact={(c) => setSelectedContact(c)}
              auvTelemetry={telemetry}
              missionTitle={currentMission.title}
              region={currentMission.region}
            />
          </div>
        </div>

        {/* ========================================================================= */}
        {/* Bottom Grid: Triage Queue + Evidence & SHAP Explainability Inspector     */}
        {/* ========================================================================= */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          {/* Left Column (5 cols): Triage List */}
          <div className="lg:col-span-5 flex flex-col">
            <TriageQueue
              contacts={contacts}
              selectedContactId={selectedContact?.contact_id || null}
              onSelectContact={(c) => setSelectedContact(c)}
            />
          </div>

          {/* Right Column (7 cols): Deep Evidence Inspector */}
          <div className="lg:col-span-7 flex flex-col">
            {selectedContact ? (
              <EvidenceCard
                contact={selectedContact}
                onReviewSubmit={handleReviewSubmit}
              />
            ) : (
              <div className="h-full min-h-[380px] flex flex-col items-center justify-center p-8 bg-slate-900/60 border border-slate-800 rounded-2xl text-center text-slate-500 font-mono text-xs">
                <Activity className="w-8 h-8 mb-2 text-cyan-500/40 animate-pulse" />
                <span>Select an acoustic contact from the waterfall, GIS map, or triage queue to inspect physical ray-tracing & SHAP attribution.</span>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* ========================================================================= */}
      {/* Upload Survey ZIP Modal                                                  */}
      {/* ========================================================================= */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-md w-full p-6 shadow-2xl flex flex-col gap-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <FolderArchive className="w-5 h-5 text-cyan-400" />
                <h3 className="text-sm font-bold text-slate-100">Upload Sonar Survey Stream (ZIP)</h3>
              </div>
              <button
                onClick={() => setShowUploadModal(false)}
                className="text-slate-400 hover:text-slate-200 text-sm"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-slate-400 leading-relaxed">
              Upload any ZIP archive containing raw sonar waterfall frames (PNG, JPG, TIF). AbyssEye will unzip, index navigation telemetry, and launch real-time acoustic streaming.
            </p>

            <div
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-slate-700 hover:border-cyan-500/80 rounded-xl p-8 flex flex-col items-center justify-center cursor-pointer bg-slate-950/50 transition group"
            >
              <Upload className="w-8 h-8 text-slate-400 group-hover:text-cyan-400 mb-2 transition" />
              <span className="text-xs font-medium text-slate-300 group-hover:text-cyan-300">
                {isUploading ? 'Extracting & Indexing Sonar Pings...' : 'Click to select .ZIP survey archive'}
              </span>
              <span className="text-[10px] text-slate-500 mt-1">Supports multi-megabyte XTF/image sequences</span>
            </div>

            <input
              type="file"
              ref={fileInputRef}
              accept=".zip"
              onChange={handleZipUpload}
              className="hidden"
            />

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
              <button
                onClick={() => setShowUploadModal(false)}
                className="px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 text-slate-300 hover:bg-slate-700"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
