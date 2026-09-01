import React, { useState, useEffect } from 'react';
import { IndianRupee, ShieldCheck, PieChart, Activity, AlertTriangle } from 'lucide-react';
import MetricCard from '../components/MetricCard';
import FailureDistribution from '../components/FailureDistribution';
import StatusBadge from '../components/StatusBadge';
import DemoControlPanel from '../components/DemoControlPanel';
import { getSimulationMetrics, fetchDemoStatus, resetDemoState, startDemoTransaction, processAnotherTransaction } from '../services/api';

export default function Dashboard({ setActiveTab }) {
  const metrics = getSimulationMetrics();
  const [demoState, setDemoState] = useState(null);
  const [loading, setLoading] = useState(false);

  // Restore backend demo status on mount (handles F5 page refresh)
  useEffect(() => {
    async function loadStatus() {
      const status = await fetchDemoStatus();
      setDemoState(status);
    }
    loadStatus();
  }, []);

  const handleReset = async () => {
    setLoading(true);
    try {
      const status = await resetDemoState();
      setDemoState(status);
    } finally {
      setLoading(false);
    }
  };

  const handleStart = async () => {
    setLoading(true);
    try {
      const status = await startDemoTransaction();
      setDemoState(status);
    } finally {
      setLoading(false);
    }
  };

  const handleProcessAnother = async () => {
    setLoading(true);
    try {
      const status = await processAnotherTransaction();
      setDemoState(status);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Interactive Hackathon Demo Control Panel */}
      <DemoControlPanel 
        demoState={demoState}
        onReset={handleReset}
        onStart={handleStart}
        onProcessAnother={handleProcessAnother}
        loading={loading}
      />

      {/* Primary KPI Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Revenue at Risk"
          value={`₹${(metrics.total_revenue_at_risk_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`}
          subtext="Evaluated across 500 payment cases"
          color="indigo"
          icon={IndianRupee}
          accent
        />
        <MetricCard
          title="Simulated Recovered"
          value={`₹${(metrics.simulated_recovered_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`}
          subtext="Authoritatively recovered revenue"
          color="emerald"
          icon={ShieldCheck}
        />
        <MetricCard
          title="Recovery Rate"
          value={`${metrics.recovery_rate_pct}%`}
          subtext="Overall conversion efficiency"
          color="cyan"
          icon={Activity}
        />
        <MetricCard
          title="Average Risk / Case"
          value={`₹${(metrics.average_risk_per_case_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`}
          subtext="Average transaction value"
          color="amber"
          icon={PieChart}
        />
      </div>

      {/* Governance Scorecard & Failure Distribution Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Governance Allowed / Denied Card */}
        <div className="glass-card p-5 rounded-xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-slate-200">OPA Governance Decisions</h3>
              <span className="text-[10px] font-mono text-slate-400">REGO POLICY ENGINE</span>
            </div>

            <div className="space-y-4 my-4">
              <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-between">
                <div>
                  <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider block">Allowed Cases</span>
                  <span className="text-2xl font-bold font-mono text-emerald-300">{metrics.governance_allowed}</span>
                </div>
                <span className="text-sm font-bold font-mono text-emerald-400">{metrics.allowed_rate_pct}%</span>
              </div>

              <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-between">
                <div>
                  <span className="text-xs font-semibold text-rose-400 uppercase tracking-wider block">Denied / Vetoed</span>
                  <span className="text-2xl font-bold font-mono text-rose-300">{metrics.governance_denied}</span>
                </div>
                <span className="text-sm font-bold font-mono text-rose-400">{metrics.denied_rate_pct}%</span>
              </div>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
            <span>Fail-Closed Security:</span>
            <span className="font-mono text-emerald-400 font-bold">ACTIVE (opa unavailable → allow=False)</span>
          </div>
        </div>

        {/* Failure Category Distribution */}
        <div className="lg:col-span-2">
          <FailureDistribution distribution={metrics.failure_distribution} />
        </div>

      </div>

    </div>
  );
}
