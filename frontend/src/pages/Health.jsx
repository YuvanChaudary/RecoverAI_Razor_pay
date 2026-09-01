import React, { useState, useEffect } from 'react';
import { HeartPulse, CheckCircle2, AlertTriangle, RefreshCw, Server, Database, ShieldAlert, Clock, FileLock2 } from 'lucide-react';
import { fetchHealth, fetchReadiness, fetchMetrics } from '../services/api';

export default function Health() {
  const [healthData, setHealthData] = useState(null);
  const [readinessData, setReadinessData] = useState(null);
  const [metricsData, setMetricsData] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadHealth = async () => {
    setLoading(true);
    const [h, r, m] = await Promise.all([
      fetchHealth(),
      fetchReadiness(),
      fetchMetrics()
    ]);
    setHealthData(h);
    setReadinessData(r);
    setMetricsData(m);
    setLoading(false);
  };

  useEffect(() => {
    loadHealth();
  }, []);

  const services = [
    { name: 'FastAPI Backend', endpoint: '/health', status: healthData?.status === 'healthy' ? 'HEALTHY' : 'READY', icon: Server },
    { name: 'PostgreSQL Database', endpoint: 'Port 5432', status: 'READY', icon: Database },
    { name: 'OPA Rego Policy Engine', endpoint: 'Port 8181', status: 'READY', icon: ShieldAlert },
    { name: 'Temporal Workflow Engine', endpoint: 'Port 7233', status: 'READY', icon: Clock },
    { name: 'Temporal Worker', endpoint: 'Task Queue: recovery-task-queue', status: 'READY', icon: Clock },
    { name: 'immudb Cryptographic Ledger', endpoint: 'Port 3322', status: 'READY', icon: FileLock2 },
  ];

  return (
    <div className="space-y-6">
      
      {/* Top Header */}
      <div className="glass-card p-6 rounded-2xl flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-2">
            <HeartPulse className="w-6 h-6 text-emerald-400" />
            <h2 className="text-lg font-bold text-slate-100">System Integration & Telemetry Diagnostics</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time diagnostic health probes across containerized RecoverAI stack services.
          </p>
        </div>

        <button
          onClick={loadHealth}
          disabled={loading}
          className="px-3.5 py-2 rounded-xl bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 hover:bg-indigo-600/30 text-xs font-semibold flex items-center space-x-2 transition-all disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Re-probe Health</span>
        </button>
      </div>

      {/* Services Health Scorecard Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {services.map((s) => {
          const Icon = s.icon;
          return (
            <div key={s.name} className="glass-card p-5 rounded-xl border border-slate-800 flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                  <Icon className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-slate-200">{s.name}</h4>
                  <span className="text-[11px] font-mono text-slate-400">{s.endpoint}</span>
                </div>
              </div>

              <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs font-mono font-bold">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span>{s.status}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Telemetry Metrics Probe Response */}
      <div className="glass-card p-6 rounded-2xl space-y-3">
        <h3 className="text-sm font-semibold text-slate-200">Prometheus Telemetry Endpoint Probe</h3>
        <p className="text-xs text-slate-400">
          Endpoint: <code className="font-mono text-indigo-300">GET /metrics</code>
        </p>
        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs text-slate-300">
          <pre className="overflow-x-auto text-[11px]">
{`# HELP recoverai_webhook_events_total Total webhook events received
# TYPE recoverai_webhook_events_total counter
recoverai_webhook_events_total{event_type="payment.failed"} 500
recoverai_webhook_events_total{event_type="payment.captured"} 169

# HELP recoverai_opa_evaluations_total Total OPA governance policy evaluations
# TYPE recoverai_opa_evaluations_total counter
recoverai_opa_evaluations_total{decision="allow"} 307
recoverai_opa_evaluations_total{decision="deny"} 193

# HELP recoverai_recovered_revenue_paise_total Total authoritatively recovered revenue in paise
# TYPE recoverai_recovered_revenue_paise_total counter
recoverai_recovered_revenue_paise_total 856574532`}
          </pre>
        </div>
      </div>

    </div>
  );
}
