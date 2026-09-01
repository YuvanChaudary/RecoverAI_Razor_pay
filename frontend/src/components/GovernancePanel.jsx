import React from 'react';
import { ShieldAlert, ShieldX, BrainCircuit, ArrowRight, Lock, AlertOctagon } from 'lucide-react';
import StatusBadge from './StatusBadge';

export default function GovernancePanel({ onSelectCase }) {
  const hostileScenario = {
    ai_confidence: 0.99,
    retry_count: 5,
    cooldown_hours: 1.0,
    required_cooldown: 24.0,
    terminal_decline: true,
    proposed_action: 'RETRY_SCHEDULED',
    failure_category: 'BANK_RISK_BLOCK',
    violations: [
      { id: 'RULE-001', name: 'Max Retries Exceeded', details: 'Retry count 5 >= 3 maximum allowed' },
      { id: 'RULE-002', name: 'Cooldown Violation', details: 'Cooldown 1.0h < 24.0h required threshold' },
      { id: 'RULE-003', name: 'Terminal Decline Lockout', details: 'Terminal bank decline prohibits retry execution' },
    ]
  };

  return (
    <div className="space-y-6">
      
      {/* Top Banner */}
      <div className="glass-card p-6 rounded-2xl border-l-4 border-l-rose-500 relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <ShieldAlert className="w-6 h-6 text-rose-400" />
              <h2 className="text-lg font-bold text-slate-100">Hostile AI Governance Demonstration</h2>
              <span className="px-2 py-0.5 text-[10px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20 rounded-md uppercase">
                SCENARIO 4
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1 max-w-2xl">
              Demonstrates that maximum AI confidence score (99%) cannot override RegTech OPA rules or force unauthorized financial execution.
            </p>
          </div>

          <div className="bg-rose-500/10 border border-rose-500/20 px-4 py-2 rounded-xl text-center shrink-0">
            <span className="text-[10px] font-bold text-rose-400 uppercase tracking-wider block">OPA VERDICT</span>
            <span className="text-xl font-bold font-mono text-rose-300">DENIED</span>
          </div>
        </div>
      </div>

      {/* Visual Pipeline Flow */}
      <div className="glass-card p-6 rounded-2xl">
        <h3 className="text-sm font-semibold text-slate-200 mb-6 flex items-center space-x-2">
          <AlertOctagon className="w-4 h-4 text-indigo-400" />
          <span>Governance Decision Boundary Pipeline</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 relative">
          
          {/* Step 1: AI Recommendation */}
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono text-slate-500 uppercase">STEP 1: PROPOSAL</span>
                <BrainCircuit className="w-4 h-4 text-cyan-400" />
              </div>
              <h4 className="text-xs font-bold text-slate-200">AI Model Prompt</h4>
              <p className="text-[11px] text-cyan-300 mt-1 font-mono">RETRY_SCHEDULED</p>
            </div>
            <div className="mt-3 pt-3 border-t border-slate-800 text-[11px]">
              <span className="text-slate-400">Claimed Confidence:</span>
              <span className="font-bold text-amber-400 font-mono ml-2">99%</span>
            </div>
          </div>

          {/* Step 2: OPA Rego Evaluation */}
          <div className="p-4 rounded-xl bg-rose-950/20 border border-rose-500/30 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono text-rose-400 uppercase">STEP 2: FIREWALL</span>
                <ShieldX className="w-4 h-4 text-rose-400" />
              </div>
              <h4 className="text-xs font-bold text-slate-200">OPA Rego Policy</h4>
              <p className="text-[11px] text-rose-300 mt-1 font-mono font-bold">VETO / DENY</p>
            </div>
            <div className="mt-3 pt-3 border-t border-rose-900/40 text-[11px]">
              <span className="text-rose-400">Violations Detected:</span>
              <span className="font-bold text-rose-300 font-mono ml-2">3 Rules</span>
            </div>
          </div>

          {/* Step 3: State Machine Boundary */}
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono text-slate-500 uppercase">STEP 3: STATE AUTHORITY</span>
                <Lock className="w-4 h-4 text-indigo-400" />
              </div>
              <h4 className="text-xs font-bold text-slate-200">State Transition</h4>
              <p className="text-[11px] text-rose-400 mt-1 font-mono font-bold">TRANSITION TO BLOCKED</p>
            </div>
            <div className="mt-3 pt-3 border-t border-slate-800 text-[11px]">
              <span className="text-slate-400">Current State:</span>
              <span className="font-mono text-slate-200 ml-2 font-bold">BLOCKED</span>
            </div>
          </div>

          {/* Step 4: Execution Outcome */}
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono text-slate-500 uppercase">STEP 4: EXECUTION</span>
                <Lock className="w-4 h-4 text-slate-500" />
              </div>
              <h4 className="text-xs font-bold text-slate-200">Razorpay / Novu</h4>
              <p className="text-[11px] text-slate-400 mt-1 font-mono">NOT EXECUTED</p>
            </div>
            <div className="mt-3 pt-3 border-t border-slate-800 text-[11px]">
              <span className="text-slate-400">Recovered Amount:</span>
              <span className="font-mono text-slate-200 ml-2 font-bold">₹0.00</span>
            </div>
          </div>

        </div>
      </div>

      {/* Violated Rego Rules Breakdown */}
      <div className="glass-card p-6 rounded-2xl">
        <h3 className="text-sm font-semibold text-slate-200 mb-4">
          Detected Rego Governance Rule Violations
        </h3>

        <div className="space-y-3">
          {hostileScenario.violations.map((v) => (
            <div key={v.id} className="p-3.5 rounded-xl bg-rose-500/5 border border-rose-500/20 flex items-start justify-between">
              <div className="flex items-start space-x-3">
                <span className="px-2 py-0.5 text-[10px] font-mono font-bold bg-rose-500/20 text-rose-300 rounded-md shrink-0">
                  {v.id}
                </span>
                <div>
                  <h4 className="text-xs font-bold text-slate-200">{v.name}</h4>
                  <p className="text-[11px] text-slate-400 mt-0.5">{v.details}</p>
                </div>
              </div>
              <span className="text-[10px] font-mono uppercase text-rose-400 font-bold shrink-0">VETO</span>
            </div>
          ))}
        </div>

        {/* Security Core Invariant Box */}
        <div className="mt-6 p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-center">
          <p className="text-xs font-semibold text-indigo-300 tracking-wide uppercase">
            🔒 Core Security Invariant: AI confidence scores cannot override OPA Rego policies or bypass state machine governance.
          </p>
        </div>
      </div>

    </div>
  );
}
