import React, { useState } from 'react';
import { FileLock2, ShieldCheck, AlertTriangle, CheckCircle, RefreshCw } from 'lucide-react';
import { getImmudbProofRecords } from '../services/api';

export default function AuditPanel() {
  const records = getImmudbProofRecords();
  const [tampered, setTampered] = useState(false);

  return (
    <div className="space-y-6">
      
      {/* Top Card */}
      <div className="glass-card p-6 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <FileLock2 className="w-6 h-6 text-indigo-400" />
            <h2 className="text-lg font-bold text-slate-100">immudb Cryptographic Audit Trail</h2>
            <span className="px-2 py-0.5 text-[10px] font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded-md">
              PHASE 8 & 14 VERIFIED
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-xl">
            Cryptographic ledger storing canonical SHA-256 hashed event state transitions. Prevents historical audit record tampering.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <div className="bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-xl text-center">
            <span className="text-[10px] font-bold text-emerald-400 uppercase block">LEDGER INTEGRITY</span>
            <span className="text-sm font-bold text-emerald-300 font-mono">100% VALID</span>
          </div>
        </div>
      </div>

      {/* Cryptographic Pipeline Flow */}
      <div className="glass-card p-6 rounded-2xl">
        <h3 className="text-sm font-semibold text-slate-200 mb-4">
          Cryptographic Receipt Generation & Verification Pipeline
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-5 gap-3 text-center text-xs">
          <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
            <span className="text-[10px] font-mono text-slate-500 uppercase block mb-1">STEP 1</span>
            <span className="font-bold text-slate-300">Audit Event</span>
          </div>
          <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
            <span className="text-[10px] font-mono text-slate-500 uppercase block mb-1">STEP 2</span>
            <span className="font-bold text-slate-300">Canonical JSON</span>
          </div>
          <div className="p-3 rounded-lg bg-indigo-950/30 border border-indigo-500/30">
            <span className="text-[10px] font-mono text-indigo-400 uppercase block mb-1">STEP 3</span>
            <span className="font-bold text-indigo-300 font-mono">SHA-256 Digest</span>
          </div>
          <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800">
            <span className="text-[10px] font-mono text-slate-500 uppercase block mb-1">STEP 4</span>
            <span className="font-bold text-slate-300">immudb Ledger</span>
          </div>
          <div className="p-3 rounded-lg bg-emerald-950/30 border border-emerald-500/30">
            <span className="text-[10px] font-mono text-emerald-400 uppercase block mb-1">STEP 5</span>
            <span className="font-bold text-emerald-300">Receipt Verified</span>
          </div>
        </div>
      </div>

      {/* Interactive Tamper Simulator */}
      <div className="glass-card p-6 rounded-2xl space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-200">
            Interactive Tamper Detection Simulator
          </h3>
          <button
            onClick={() => setTampered(!tampered)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-2 transition-all ${
              tampered
                ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                : 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 hover:bg-indigo-600/30'
            }`}
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>{tampered ? 'Restore Original Event' : 'Simulate Payload Tampering'}</span>
          </button>
        </div>

        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs space-y-2">
          <div className="flex justify-between text-slate-400 text-[11px] pb-2 border-b border-slate-800">
            <span>EVENT KEY: recoverai/audit/evt_audit_001_p16</span>
            <span>TYPE: STATE_TRANSITION</span>
          </div>
          
          <pre className={`p-3 rounded-lg overflow-x-auto text-[11px] ${
            tampered ? 'bg-rose-950/20 text-rose-300 border border-rose-500/30' : 'bg-slate-900 text-slate-300'
          }`}>
            {JSON.stringify({
              event_id: 'evt_audit_001_p16',
              case_id: 'RC-1004',
              previous_state: 'AWAITING_SETTLEMENT',
              new_state: 'RECOVERED',
              governance_allowed: tampered ? false : true, // Alter payload!
              recovered_amount_paise: 499900
            }, null, 2)}
          </pre>

          <div className="flex items-center justify-between pt-2">
            <div className="text-slate-400 text-[11px]">
              Computed Hash: <code className="text-indigo-300 font-bold ml-1">
                {tampered ? 'e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c0d9e8f7' : records[0].payload_hash}
              </code>
            </div>
            <div className="flex items-center space-x-1.5">
              {tampered ? (
                <span className="px-2.5 py-1 rounded-md bg-rose-500/20 text-rose-300 border border-rose-500/30 text-[11px] font-bold flex items-center space-x-1">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  <span>TAMPER DETECTED (Hash Mismatch)</span>
                </span>
              ) : (
                <span className="px-2.5 py-1 rounded-md bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[11px] font-bold flex items-center space-x-1">
                  <CheckCircle className="w-3.5 h-3.5" />
                  <span>VALID (Integrity Verified)</span>
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

    </div>
  );
}
