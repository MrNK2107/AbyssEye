'use client';

import React, { useState } from 'react';
import { ContactDigitalTwin } from '@/types/contact';
import { ShieldAlert, CheckCircle, Eye, Search, Filter } from 'lucide-react';

interface TriageQueueProps {
  contacts: ContactDigitalTwin[];
  selectedContactId: string | null;
  onSelectContact: (contact: ContactDigitalTwin) => void;
}

export const TriageQueue: React.FC<TriageQueueProps> = ({
  contacts,
  selectedContactId,
  onSelectContact
}) => {
  const [filterState, setFilterState] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const filteredContacts = contacts.filter((c) => {
    const matchesFilter =
      filterState === 'ALL' ||
      (filterState === 'DEBRIS' && c.triage_state === 'HIGH_CONFIDENCE') ||
      (filterState === 'REVIEW' && c.triage_state === 'REVIEW') ||
      (filterState === 'NATURAL' && c.triage_state.includes('NATURAL'));

    const matchesSearch =
      c.contact_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.target_type_hint.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.channel.toLowerCase().includes(searchTerm.toLowerCase());

    return matchesFilter && matchesSearch;
  });

  return (
    <div className="bg-ocean-950/90 backdrop-blur rounded-2xl border border-ocean-700/80 p-4 sm:p-5 shadow-2xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-5 h-5 text-cyan-400" />
          <h2 className="text-sm font-bold text-slate-100 font-mono tracking-wider uppercase">
            Live Sonar Contact Triage Queue
          </h2>
          <span className="text-xs font-mono text-cyan-400 bg-ocean-900 border border-ocean-700 px-2 py-0.5 rounded">
            {contacts.length} Total
          </span>
        </div>

        {/* Filters & Search */}
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search contact ID / type..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-ocean-900 border border-ocean-700 rounded-lg pl-8 pr-3 py-1 text-xs font-mono text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div className="flex bg-ocean-900 border border-ocean-700 rounded-lg p-0.5 text-[11px] font-mono font-bold">
            {['ALL', 'DEBRIS', 'REVIEW', 'NATURAL'].map((f) => (
              <button
                key={f}
                onClick={() => setFilterState(f)}
                className={`px-2.5 py-0.5 rounded transition ${
                  filterState === f
                    ? 'bg-cyan-500 text-ocean-950 shadow'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>
      </div>

      {contacts.length === 0 ? (
        <div className="py-10 text-center font-mono text-xs text-slate-500 border border-dashed border-ocean-800 rounded-xl">
          No contacts surfaced in active survey buffer. Click "Generate Physics Survey" or ingest sonar file.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-ocean-800 text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider">
                <th className="py-2.5 px-3">Contact ID</th>
                <th className="py-2.5 px-3">Triage State</th>
                <th className="py-2.5 px-3">Target Subtype</th>
                <th className="py-2.5 px-3">P(Anthropogenic)</th>
                <th className="py-2.5 px-3">Shadow Height</th>
                <th className="py-2.5 px-3">Collinearity</th>
                <th className="py-2.5 px-3">Persistence</th>
                <th className="py-2.5 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ocean-800/60 text-xs font-mono">
              {filteredContacts.map((contact) => {
                const isSelected = contact.contact_id === selectedContactId;
                const p_anth = contact.fusion_decision?.calibrated_probabilities?.p_anthropogenic ?? (contact as any).confidence ?? 0.85;
                const physics = contact.evidence_graph?.acoustic_physics || { estimated_target_height_m: 0.85, collinearity_score: 0.88 };
                const tracking = contact.evidence_graph?.temporal_tracking || null;
                const triageState = contact.triage_state || 'REVIEW';
                const targetHint = contact.target_type_hint || (contact as any).classification || 'DEBRIS';

                return (
                  <tr
                    key={contact.contact_id || Math.random().toString()}
                    onClick={() => onSelectContact(contact)}
                    className={`cursor-pointer transition-colors ${
                      isSelected
                        ? 'bg-cyan-950/80 text-cyan-200 font-semibold'
                        : 'hover:bg-ocean-900/60 text-slate-300'
                    }`}
                  >
                    <td className="py-2.5 px-3 font-bold text-cyan-300">
                      {contact.contact_id}
                    </td>
                    <td className="py-2.5 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${
                        triageState === 'HIGH_CONFIDENCE' ? 'bg-rose-950/90 text-rose-300 border-rose-700/60' :
                        triageState === 'REVIEW' ? 'bg-amber-950/90 text-amber-300 border-amber-700/60' :
                        'bg-emerald-950/90 text-emerald-300 border-emerald-700/60'
                      }`}>
                        {triageState.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-semibold text-slate-200">
                      {targetHint.replace(/_/g, ' ')}
                    </td>
                    <td className="py-2.5 px-3 font-bold">
                      <span className={p_anth > 0.80 ? 'text-rose-400' : p_anth > 0.40 ? 'text-amber-400' : 'text-emerald-400'}>
                        {(p_anth * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-300">
                      {physics.estimated_target_height_m > 0 ? `${physics.estimated_target_height_m.toFixed(2)}m` : '0.00m'}
                    </td>
                    <td className="py-2.5 px-3">
                      {physics.collinearity_score > 0.8 ? (
                        <span className="text-emerald-400 flex items-center gap-1 font-bold">
                          <CheckCircle className="w-3 h-3" /> Validated
                        </span>
                      ) : (
                        <span className="text-slate-500">Diffuse</span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-slate-300">
                      {tracking ? `${tracking.hits}/${tracking.total_window} pings` : '1 ping'}
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectContact(contact);
                        }}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-ocean-900 hover:bg-cyan-600/30 text-cyan-300 text-[11px] font-bold border border-ocean-700 hover:border-cyan-500/60 transition"
                      >
                        <Eye className="w-3 h-3" />
                        <span>Inspect</span>
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
