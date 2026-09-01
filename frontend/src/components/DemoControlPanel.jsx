import { 
  RotateCcw, 
  Play, 
  Plus,
  ShieldCheck, 
  BrainCircuit, 
  Clock, 
  CheckCircle2, 
  AlertCircle, 
  Lock, 
  Layers, 
  FileCheck, 
  IndianRupee 
} from 'lucide-react';

export default function DemoControlPanel({ demoState, onReset, onStart, onProcessAnother, loading }) {
  const isProcessing = demoState?.is_processing || loading;
  const tracker = demoState?.lifecycle_tracker || {};
  const currentState = demoState?.state || 'READY';

  const stages = [
    { key: 'DETECTED', label: '1. Detected' },
    { key: 'DIAGNOSED', label: '2. Diagnosed' },
    { key: 'AI_DECISION', label: '3. AI Decision' },
    { key: 'OPA_APPROVED', label: '4. OPA Approved' },
    { key: 'ACTION_SCHEDULED', label: '5. Scheduled' },
    { key: 'ACTION_EXECUTED', label: '6. Executed' },
    { key: 'AWAITING_SETTLEMENT', label: '7. Settlement' },
    { key: 'RECOVERED', label: '8. Recovered' },
  ];

  return (
    <div className="space-y-6">
      
      {/* Primary Control Header Card */}
      <div className="glass-card p-6 rounded-2xl border-l-4 border-l-cyan-500 shadow-xl bg-gradient-to-r from-slate-900/90 via-slate-900/60 to-slate-950/90">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          
          <div>
            <div className="flex items-center space-x-2.5">
              <span className="px-2.5 py-1 text-xs font-mono font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 rounded-lg uppercase tracking-wider">
                SAFE SYNTHETIC DEMO
              </span>
              <span className="text-xs text-slate-400 font-mono">
                No Real Financial Mutations
              </span>
              {demoState?.total_cases > 0 && (
                <span className="px-2 py-0.5 text-xs font-mono font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 rounded-md">
                  Cases Processed: {demoState.total_cases}
                </span>
              )}
            </div>
            <h2 className="text-xl font-extrabold text-slate-100 mt-1.5 tracking-tight">
              Interactive Revenue Recovery Lifecycle
            </h2>
            <p className="text-xs text-slate-400 mt-1 max-w-2xl">
              Demonstrate the complete autonomous pipeline: failure ingestion → AI strategy → OPA firewall → Temporal saga → Razorpay HMAC settlement → immudb audit.
            </p>
          </div>

          {/* Interactive Control Buttons */}
          <div className="flex items-center space-x-2.5 shrink-0">
            <button
              onClick={onReset}
              disabled={isProcessing}
              className="px-3.5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 border border-slate-700 text-xs font-bold flex items-center space-x-1.5 transition-all shadow-md active:scale-95"
            >
              <RotateCcw className={`w-4 h-4 text-cyan-400 ${isProcessing ? 'animate-spin' : ''}`} />
              <span>↻ RESET DEMO</span>
            </button>

            <button
              onClick={onStart}
              disabled={isProcessing}
              className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 disabled:opacity-50 text-white font-bold text-xs flex items-center space-x-1.5 transition-all shadow-lg shadow-indigo-500/25 active:scale-95"
            >
              <Play className="w-4 h-4 text-white fill-white" />
              <span>{isProcessing ? 'PROCESSING...' : '▶ START DEMO'}</span>
            </button>

            <button
              onClick={onProcessAnother}
              disabled={isProcessing}
              className="px-4 py-2.5 rounded-xl bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/40 disabled:opacity-50 font-bold text-xs flex items-center space-x-1.5 transition-all shadow-md active:scale-95"
            >
              <Plus className="w-4 h-4 text-emerald-400" />
              <span>+ PROCESS ANOTHER</span>
            </button>
          </div>

        </div>

        {/* Live KPI Metric Strip */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-6 pt-5 border-t border-slate-800/80">
          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
            <span className="text-[10px] font-mono font-semibold text-slate-400 uppercase tracking-wider block">
              Revenue at Risk
            </span>
            <span className="text-xl font-extrabold font-mono text-indigo-300">
              {demoState?.revenue_at_risk_formatted || '₹0.00'}
            </span>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
            <span className="text-[10px] font-mono font-semibold text-slate-400 uppercase tracking-wider block">
              Recovered Amount
            </span>
            <span className="text-xl font-extrabold font-mono text-emerald-400">
              {demoState?.recovered_amount_formatted || '₹0.00'}
            </span>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800">
            <span className="text-[10px] font-mono font-semibold text-slate-400 uppercase tracking-wider block">
              Recovery Conversion
            </span>
            <span className="text-xl font-extrabold font-mono text-cyan-300">
              {demoState?.recovery_rate_pct ? `${demoState.recovery_rate_pct}%` : '0%'}
            </span>
          </div>
        </div>

        {/* 8-Stage Lifecycle Tracker Strip */}
        <div className="mt-6 pt-4 border-t border-slate-800/80">
          <div className="text-[11px] font-mono font-semibold text-slate-400 uppercase tracking-wider mb-3">
            Autonomous Pipeline Lifecycle Tracker: <span className="text-indigo-400 font-bold">{currentState}</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
            {stages.map((st) => {
              const active = tracker[st.key];
              const isCurrent = currentState === st.key;
              return (
                <div
                  key={st.key}
                  className={`p-2.5 rounded-xl text-center border transition-all ${
                    active
                      ? isCurrent
                        ? 'bg-indigo-600/30 border-indigo-400 text-indigo-200 ring-2 ring-indigo-500/40 shadow-lg shadow-indigo-500/20'
                        : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                      : 'bg-slate-950/40 border-slate-800 text-slate-500'
                  }`}
                >
                  <div className="flex items-center justify-center space-x-1 mb-1">
                    {active ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                    ) : (
                      <span className="w-2 h-2 rounded-full bg-slate-700" />
                    )}
                  </div>
                  <span className="text-[11px] font-bold block truncate">
                    {st.label}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

      </div>

      {/* Stage Detail Cards Grid (Only rendered when demo active) */}
      {demoState?.failure_details && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          
          {/* AI Strategy Card */}
          <div className="glass-card p-4 rounded-xl border border-indigo-500/20 flex flex-col justify-between">
            <div>
              <div className="flex items-center space-x-2 mb-2">
                <BrainCircuit className="w-4 h-4 text-indigo-400" />
                <span className="text-xs font-bold text-indigo-300">AI Strategy Proposal</span>
              </div>
              <p className="text-xs font-mono text-slate-300">Action: {demoState.ai_proposal?.recommended_action}</p>
              <p className="text-xs font-mono text-slate-400">Cooldown: {demoState.ai_proposal?.cooldown_hours}h</p>
              <p className="text-xs font-mono text-slate-400">Confidence: {(demoState.ai_proposal?.confidence * 100).toFixed(0)}%</p>
            </div>
            <div className="mt-3 pt-2 border-t border-slate-800 text-[10px] font-mono text-amber-400">
              PROPOSAL ONLY — AI cannot execute funds
            </div>
          </div>

          {/* OPA Governance Card */}
          <div className="glass-card p-4 rounded-xl border border-rose-500/20 flex flex-col justify-between">
            <div>
              <div className="flex items-center space-x-2 mb-2">
                <ShieldCheck className="w-4 h-4 text-rose-400" />
                <span className="text-xs font-bold text-rose-300">OPA Policy Engine</span>
              </div>
              <p className="text-xs font-mono text-slate-300">Decision: {demoState.opa_decision?.decision}</p>
              <p className="text-xs font-mono text-slate-400">Violations: {demoState.opa_decision?.violations?.length || 0}</p>
              <p className="text-xs font-mono text-slate-400">Rules: RULE-001, 002, 003</p>
            </div>
            <div className="mt-3 pt-2 border-t border-slate-800 text-[10px] font-mono text-emerald-400">
              FAIL-CLOSED POLICY FIREWALL
            </div>
          </div>

          {/* Temporal Saga Card */}
          <div className="glass-card p-4 rounded-xl border border-cyan-500/20 flex flex-col justify-between">
            <div>
              <div className="flex items-center space-x-2 mb-2">
                <Clock className="w-4 h-4 text-cyan-400" />
                <span className="text-xs font-bold text-cyan-300">Temporal Workflow</span>
              </div>
              <p className="text-xs font-mono text-slate-300">Status: {demoState.temporal_status?.status}</p>
              <p className="text-xs font-mono text-slate-400 truncate">ID: {demoState.temporal_status?.workflow_id}</p>
              <p className="text-xs font-mono text-slate-400">Timer: workflow.sleep(48h)</p>
            </div>
            <div className="mt-3 pt-2 border-t border-slate-800 text-[10px] font-mono text-cyan-400">
              DURABLE SAGA ORCHESTRATION
            </div>
          </div>

          {/* Authoritative Settlement & immudb Audit Card */}
          <div className="glass-card p-4 rounded-xl border border-emerald-500/20 flex flex-col justify-between">
            <div>
              <div className="flex items-center space-x-2 mb-2">
                <FileCheck className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-bold text-emerald-300">Settlement & Audit</span>
              </div>
              <p className="text-xs font-mono text-slate-300">Event: payment.captured</p>
              <p className="text-xs font-mono text-slate-400">HMAC: Verified ✓</p>
              <p className="text-xs font-mono text-slate-400">immudb: SHA-256 Valid</p>
            </div>
            <div className="mt-3 pt-2 border-t border-slate-800 text-[10px] font-mono text-emerald-400">
              AUTHORITATIVE RECOVERY CONFIRMED
            </div>
          </div>

        </div>
      )}

    </div>
  );
}
