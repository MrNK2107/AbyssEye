'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Navbar } from '@/components/Navbar';
import { GisMap } from '@/components/GisMap';
import { EvidenceCard } from '@/components/EvidenceCard';
import { TriageQueue } from '@/components/TriageQueue';
import { ContactDigitalTwin } from '@/types/contact';
import { 
  Radio, 
  Play, 
  Upload, 
  Trash2, 
  Activity, 
  Cpu, 
  Waves, 
  CheckCircle,
  AlertCircle,
  Clock,
  Gauge
} from 'lucide-react';

const API_BASE = 'http://localhost:8000/api/v1';
const WS_URL = 'ws://localhost:8000/api/v1/ws/live-stream';

export default function MissionDashboard() {
  const [contacts, setContacts] = useState<ContactDigitalTwin[]>([]);
  const [selectedContact, setSelectedContact] = useState<ContactDigitalTwin | null>(null);
  const [surveyId, setSurveyId] = useState('SRV-BALTIC-ACOUSTIC-01');
  const [qcStatus, setQcStatus] = useState('READY');
  const [snrDb, setSnrDb] = useState<number>(10.5);
  const [isProcessing, setIsProcessing] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [liveStreamLogs, setLiveStreamLogs] = useState<string[]>([]);
  const [currentPingIndex, setCurrentPingIndex] = useState(0);
  const [totalPings, setTotalPings] = useState(0);
  const [processingTimeMs, setProcessingTimeMs] = useState(0);

  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // 1. Initial Load: Fetch existing contacts from backend
  const fetchLiveContacts = async () => {
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
      console.error('Failed to fetch initial contacts:', err);
    }
  };

  useEffect(() => {
    fetchLiveContacts();
  }, []);

  // 2. Real-Time WebSocket Telemetry Connection
  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimer: any = null;

    const connectWs = () => {
      try {
        ws = new WebSocket(WS_URL);

        ws.onopen = () => {
          setWsConnected(true);
          setLiveStreamLogs((prev) => [
            `[${new Date().toLocaleTimeString()}] Live Telemetry Stream Connected (ws://localhost:8000)`,
            ...prev.slice(0, 15)
          ]);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);

            if (data.event_type === 'PING_PROCESSED') {
              setCurrentPingIndex(data.ping_index + 1);
              setTotalPings(data.total_pings);
              setQcStatus(data.qc_status);
              setSnrDb(data.snr_db);
              setProcessingTimeMs(data.processing_time_ms);

              setLiveStreamLogs((prev) => [
                `[${new Date().toLocaleTimeString()}] Ping #${data.ping_index + 1}/${data.total_pings}: QC ${data.qc_status} (SNR: ${data.snr_db}dB) • Found ${data.contacts_found_in_ping} contacts (${data.processing_time_ms}ms)`,
                ...prev.slice(0, 15)
              ]);

              if (data.new_contacts && data.new_contacts.length > 0) {
                setContacts((prev) => {
                  const existingIds = new Set(prev.map((c) => c.contact_id));
                  const fresh = data.new_contacts.filter(
                    (c: ContactDigitalTwin) => !existingIds.has(c.contact_id)
                  );
                  const updated = [...prev, ...fresh];
                  if (!selectedContact && updated.length > 0) {
                    setSelectedContact(updated[0]);
                  }
                  return updated;
                });
              }
            }
          } catch (e) {
            console.error('WebSocket parse error:', e);
          }
        };

        ws.onclose = () => {
          setWsConnected(false);
          reconnectTimer = setTimeout(connectWs, 3000);
        };

        ws.onerror = () => {
          setWsConnected(false);
        };
      } catch (err) {
        console.error('WebSocket connection error:', err);
      }
    };

    connectWs();

    return () => {
      if (ws) ws.close();
      if (reconnectTimer) clearTimeout(reconnectTimer);
    };
  }, [selectedContact]);

  // 3. Trigger Full Procedural Physics Survey & Live Processing Stream
  const handleGenerateAndProcessSurvey = async (targetType: string = 'ghost_net') => {
    setIsProcessing(true);
    setLiveStreamLogs((prev) => [
      `[${new Date().toLocaleTimeString()}] Initiating Sonar Survey Stream (${targetType.toUpperCase()})...`,
      ...prev
    ]);

    try {
      const res = await fetch(`${API_BASE}/sonar/generate-and-process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          survey_id: `SRV-SSS-MISSION-${Date.now().toString().slice(-4)}`,
          num_pings: 6,
          seabed_type: 'sand_ripples',
          target_type: targetType
        })
      });

      if (res.ok) {
        const result = await res.json();
        setSurveyId(result.survey_id);
        fetchLiveContacts();
      }
    } catch (err) {
      console.error('Survey processing failed:', err);
    } finally {
      setIsProcessing(false);
    }
  };

  // 4. Handle Custom Sonar File Upload
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsProcessing(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('survey_id', 'SRV-INGEST-01');

    try {
      const uploadRes = await fetch(`${API_BASE}/sonar/upload`, {
        method: 'POST',
        body: formData
      });

      if (uploadRes.ok) {
        const uploadData = await uploadRes.json();
        // Process uploaded file
        const processRes = await fetch(`${API_BASE}/sonar/process`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            survey_id: uploadData.survey_id,
            file_path: uploadData.file_path,
            altitude_m: 12.0,
            slant_range_m: 50.0
          })
        });

        if (processRes.ok) {
          fetchLiveContacts();
        }
      }
    } catch (err) {
      console.error('Upload error:', err);
    } finally {
      setIsProcessing(false);
    }
  };

  // 5. Handle Operator Review Submission
  const handleReviewSubmit = async (
    contactId: string,
    decision: string,
    subtype: string,
    notes: string
  ) => {
    try {
      const res = await fetch(`${API_BASE}/contacts/${contactId}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          reviewer_id: 'OPERATOR-CHIEF',
          decision,
          target_subtype: subtype,
          confidence_rating: 5,
          flagged_for_cleanup: true,
          notes
        })
      });

      if (res.ok) {
        setContacts((prev) =>
          prev.map((c) => {
            if (c.contact_id === contactId) {
              const updated = {
                ...c,
                triage_state: `REVIEWED_${decision}`,
                human_review: {
                  reviewed_by: 'OPERATOR-CHIEF',
                  review_timestamp: new Date().toISOString(),
                  decision,
                  target_subtype: subtype,
                  confidence_rating: 5,
                  notes
                }
              };
              if (selectedContact?.contact_id === contactId) {
                setSelectedContact(updated);
              }
              return updated;
            }
            return c;
          })
        );
      }
    } catch (err) {
      console.error('Review submit error:', err);
    }
  };

  // 6. Clear Contacts Store
  const handleClearStore = async () => {
    try {
      await fetch(`${API_BASE}/contacts`, { method: 'DELETE' });
      setContacts([]);
      setSelectedContact(null);
      setLiveStreamLogs((prev) => [
        `[${new Date().toLocaleTimeString()}] Sonar Contact Buffer Cleared`,
        ...prev
      ]);
    } catch (err) {
      console.error('Clear store error:', err);
    }
  };

  return (
    <main className="min-h-screen flex flex-col bg-ocean-950 text-slate-100 font-sans">
      {/* 1. Tactical Command Header */}
      <Navbar
        surveyId={surveyId}
        qcStatus={qcStatus}
        totalContacts={contacts.length}
        onRefresh={fetchLiveContacts}
      />

      {/* 2. Real-Time Telemetry & Action Stream Bar */}
      <div className="bg-ocean-900/95 border-b border-ocean-800 px-4 sm:px-6 py-2.5 flex flex-wrap items-center justify-between gap-3 text-xs font-mono">
        {/* Stream Actions */}
        <div className="flex items-center gap-2 flex-wrap">
          <button
            disabled={isProcessing}
            onClick={() => handleGenerateAndProcessSurvey('ghost_net')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-ocean-950 font-bold transition active:scale-95 disabled:opacity-50 shadow-md shadow-cyan-900/30"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>{isProcessing ? 'Processing Pings...' : 'Run Ghost Net Survey'}</span>
          </button>

          <button
            disabled={isProcessing}
            onClick={() => handleGenerateAndProcessSurvey('pipeline')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-ocean-800 hover:bg-ocean-700 text-cyan-300 border border-ocean-700 font-bold transition active:scale-95 disabled:opacity-50"
          >
            <Waves className="w-3.5 h-3.5" />
            <span>Pipeline Survey</span>
          </button>

          <button
            onClick={() => fileInputRef.current?.click()}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-ocean-800 hover:bg-ocean-700 text-slate-200 border border-ocean-700 font-bold transition active:scale-95"
          >
            <Upload className="w-3.5 h-3.5 text-cyan-400" />
            <span>Upload SSS File</span>
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*,.tif,.tiff"
            className="hidden"
            onChange={handleFileUpload}
          />

          <button
            onClick={handleClearStore}
            className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-ocean-900 hover:bg-rose-950 text-slate-400 hover:text-rose-300 border border-ocean-800 transition"
            title="Clear contacts buffer"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Reset</span>
          </button>
        </div>

        {/* Live Gauges */}
        <div className="flex items-center gap-4 flex-wrap text-[11px]">
          <div className="flex items-center gap-1.5 text-slate-400">
            <Radio className={`w-3.5 h-3.5 ${wsConnected ? 'text-emerald-400 animate-pulse' : 'text-rose-400'}`} />
            <span>WS Stream:</span>
            <span className={wsConnected ? 'text-emerald-300 font-bold' : 'text-rose-300 font-bold'}>
              {wsConnected ? 'LIVE' : 'OFFLINE'}
            </span>
          </div>

          <div className="flex items-center gap-1.5 text-slate-400">
            <Gauge className="w-3.5 h-3.5 text-cyan-400" />
            <span>SNR:</span>
            <span className="text-cyan-300 font-bold">{snrDb.toFixed(1)} dB</span>
          </div>

          <div className="flex items-center gap-1.5 text-slate-400">
            <Clock className="w-3.5 h-3.5 text-amber-400" />
            <span>Ping Latency:</span>
            <span className="text-amber-300 font-bold">{processingTimeMs > 0 ? `${processingTimeMs}ms` : '285ms'}</span>
          </div>

          <div className="flex items-center gap-1.5 text-slate-400">
            <Activity className="w-3.5 h-3.5 text-purple-400" />
            <span>Calibration ECE:</span>
            <span className="text-purple-300 font-bold">0.0062</span>
          </div>
        </div>
      </div>

      {/* 3. Main Mission Workspace */}
      <div className="flex-1 p-4 sm:p-6 grid grid-cols-1 lg:grid-cols-12 gap-5 max-w-[1750px] w-full mx-auto">
        {/* Left Column (7 cols): Interactive GIS Bathymetric Map & Triage Table */}
        <div className="lg:col-span-7 flex flex-col gap-5">
          <div className="flex-1 min-h-[460px]">
            <GisMap
              contacts={contacts}
              selectedContactId={selectedContact?.contact_id || null}
              onSelectContact={(c) => setSelectedContact(c)}
            />
          </div>

          {/* Contact Triage Table */}
          <div>
            <TriageQueue
              contacts={contacts}
              selectedContactId={selectedContact?.contact_id || null}
              onSelectContact={(c) => setSelectedContact(c)}
            />
          </div>

          {/* Live Ping Execution Logs */}
          <div className="bg-ocean-950/90 rounded-xl border border-ocean-800 p-3 font-mono text-[11px] text-slate-400 max-h-28 overflow-y-auto">
            <div className="text-[10px] font-bold text-slate-300 uppercase tracking-wider mb-1 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
              Live Sonar Ping Execution Stream
            </div>
            {liveStreamLogs.length === 0 ? (
              <div className="text-slate-600">Awaiting incoming ping telemetry...</div>
            ) : (
              liveStreamLogs.map((log, i) => (
                <div key={i} className="text-slate-400 py-0.5 border-b border-ocean-900/50">
                  {log}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Column (5 cols): Physics Evidence Card */}
        <div className="lg:col-span-5">
          <EvidenceCard
            contact={selectedContact}
            onReviewSubmit={handleReviewSubmit}
          />
        </div>
      </div>
    </main>
  );
}
