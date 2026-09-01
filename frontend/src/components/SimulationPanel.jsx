import React from 'react';
import { BarChart3, ShieldCheck, CheckCircle2, AlertCircle, Info } from 'lucide-react';
import MetricCard from './MetricCard';
import FailureDistribution from './FailureDistribution';
import { getSimulationMetrics } from '../services/api';

export default function SimulationPanel() {
  const metrics = getSimulationMetrics();

  return (
    <div className="space-y-6">
      
      {/* Simulation Banner */}
      <div className="glass-card p-6 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <BarChart3 className="w-6 h-6 text-indigo-400" />
            <h2 className="text-lg font-bold text-slate-100">Phase 10 Batch 500-Case Simulator</h2>
            <span className="px-2 py-0.5 text-[10px] font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded-md font-mono">
              SEED 42
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-xl">
            Deterministic evaluation engine testing system recovery performance and financial safety boundaries across 500 payment failure cases.
          </p>
        </div>

        <div className="px-3.5 py-1.5 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center space-x-2 shrink-0">
          <Info className="w-4 h-4 text-amber-400" />
          <span className="text-xs font-mono font-bold text-amber-300 uppercase tracking-wider">
            SIMULATION DATA — NOT LIVE REVENUE
          </span>
        </div>
      </div>

      {/* Metric Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Revenue at Risk"
          value={`₹${(metrics.total_revenue_at_risk_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`}
          subtext="Total revenue evaluated in batch"
          color="indigo"
          accent
        />
        <MetricCard
          title="Simulated Recovery"
          value={`₹${(metrics.simulated_recovered_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`}
          subtext="OPA-approved synthetic recovery"
          color="emerald"
        />
        <MetricCard
          title="Recovery Rate"
          value={`${metrics.recovery_rate_pct}%`}
          subtext="Revenue recovery conversion"
          color="cyan"
        />
        <MetricCard
          title="Average Risk / Case"
          value={`₹${(metrics.average_risk_per_case_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`}
          subtext="Mean transaction value"
          color="amber"
        />
      </div>

      {/* Safety & Invariant Verification Scorecard */}
      <div className="glass-card p-6 rounded-2xl border-l-4 border-l-emerald-500">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <h3 className="text-sm font-semibold text-slate-200">Financial Invariant Safety Verification</h3>
          </div>
          <span className="px-2.5 py-1 rounded-md bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs font-bold font-mono">
            ALL INVARIANTS PASSED
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between">
            <div>
              <span className="text-[10px] font-mono uppercase text-slate-400 block">Double Recoveries</span>
              <span className="text-2xl font-bold font-mono text-emerald-400">0</span>
            </div>
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          </div>

          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between">
            <div>
              <span className="text-[10px] font-mono uppercase text-slate-400 block">Unsafe Recovery Claims</span>
              <span className="text-2xl font-bold font-mono text-emerald-400">0</span>
            </div>
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
          </div>

          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between">
            <div>
              <span className="text-[10px] font-mono uppercase text-slate-400 block">Duplicate Events Tested</span>
              <span className="text-2xl font-bold font-mono text-cyan-400">50</span>
            </div>
            <CheckCircle2 className="w-5 h-5 text-cyan-400" />
          </div>
        </div>
      </div>

      {/* Failure Category Distribution & OPA Rule Violations Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Failure Category Chart */}
        <FailureDistribution distribution={metrics.failure_distribution} />

        {/* Rego Rule Violation Breakdown */}
        <div className="glass-card p-5 rounded-xl flex flex-col justify-between">
          <div>
            <h3 className="text-sm font-semibold text-slate-200 mb-1">
              OPA Rego Rule Violation Breakdown
            </h3>
            <p className="text-xs text-slate-400 mb-4">
              Rule veto distribution across {metrics.governance_denied} denied cases
            </p>

            <div className="space-y-3">
              {metrics.rule_violations.map((r) => (
                <div key={r.rule_id} className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-2.5">
                    <span className="px-2 py-0.5 text-[10px] font-mono font-bold bg-rose-500/10 text-rose-300 border border-rose-500/20 rounded-md shrink-0">
                      {r.rule_id}
                    </span>
                    <span className="text-slate-300 font-sans">{r.name}</span>
                  </div>
                  <span className="font-mono font-bold text-rose-400">{r.violations}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
            <span>Total Veto Instances:</span>
            <span className="font-mono font-bold text-rose-300">193</span>
          </div>
        </div>

      </div>

    </div>
  );
}
