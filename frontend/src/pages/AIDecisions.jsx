import React from 'react';
import { BrainCircuit, ShieldAlert, AlertTriangle } from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import { getSyntheticRecoveryCases } from '../services/api';

export default function AIDecisions() {
  const cases = getSyntheticRecoveryCases();

  return (
    <div className="space-y-6">
      
      {/* Top Banner */}
      <div className="glass-card p-6 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <BrainCircuit className="w-6 h-6 text-indigo-400" />
            <h2 className="text-lg font-bold text-slate-100">NVIDIA NIM AI Recommendation Engine</h2>
            <span className="px-2 py-0.5 text-[10px] font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded-md font-mono">
              NEMOTRON-3 SUPER 120B
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-xl">
            Generates intelligent recovery action proposals with XML prompt-injection defenses and low-confidence fallback strategies.
          </p>
        </div>
      </div>

      {/* Prominent Mandatory AI Disclaimer Box */}
      <div className="p-5 rounded-2xl bg-gradient-to-r from-amber-500/15 via-indigo-500/15 to-purple-500/15 border border-amber-500/30 text-amber-200 space-y-2">
        <div className="flex items-center space-x-2">
          <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />
          <h3 className="text-sm font-bold uppercase tracking-wider text-amber-300">
            Mandatory Architectural Boundary
          </h3>
        </div>
        <p className="text-xs font-sans leading-relaxed text-slate-300">
          <strong>AI proposes actions. AI does NOT authorize financial execution.</strong> All AI recommendations are strictly evaluated by Open Policy Agent (OPA) Rego rules and enforced by the Authoritative State Machine. Maximum AI confidence scores cannot override governance vetos.
        </p>
      </div>

      {/* AI Decision Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {cases.map((c) => (
          <div key={c.case_id} className="glass-card p-5 rounded-xl border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-[10px] font-mono text-indigo-400 uppercase tracking-widest block">{c.case_id}</span>
                <h4 className="text-sm font-bold text-slate-200">{c.failure_category}</h4>
              </div>
              <div className="text-right">
                <span className="text-[10px] font-mono text-slate-500 uppercase block">AI CONFIDENCE</span>
                <span className="text-lg font-bold font-mono text-amber-400">{(c.ai_confidence * 100).toFixed(0)}%</span>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs space-y-1.5 font-mono">
              <div className="flex justify-between">
                <span className="text-slate-400">Proposed Action:</span>
                <span className="text-cyan-300 font-bold">{c.proposed_action}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Payment Amount:</span>
                <span className="text-slate-200">₹{(c.amount_paise / 100).toLocaleString('en-IN')}</span>
              </div>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-slate-800 text-xs">
              <span className="text-slate-400">OPA Governance Verdict:</span>
              <StatusBadge type="opa" value={c.opa_decision} />
            </div>
          </div>
        ))}
      </div>

    </div>
  );
}
