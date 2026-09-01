import React from 'react';
import { 
  ShieldAlert, 
  Activity, 
  BrainCircuit, 
  CheckCircle2, 
  BarChart3, 
  FileLock2, 
  HeartPulse, 
  Layers,
  RotateCcw
} from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab }) {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: Activity },
    { id: 'cases', label: 'Recovery Cases', icon: Layers },
    { id: 'ai', label: 'AI Decisions', icon: BrainCircuit },
    { id: 'governance', label: 'Governance (OPA)', icon: ShieldAlert },
    { id: 'simulation', label: 'Simulation (500)', icon: BarChart3 },
    { id: 'audit', label: 'Audit Trail', icon: FileLock2 },
    { id: 'health', label: 'System Health', icon: HeartPulse },
  ];

  return (
    <header className="glass-panel sticky top-0 z-50 border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Brand Logo & Name */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('overview')}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 p-0.5 shadow-lg shadow-indigo-500/20">
              <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                <ShieldAlert className="w-5 h-5 text-indigo-400" />
              </div>
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-slate-200 to-indigo-300 bg-clip-text text-transparent">
                  RecoverAI
                </span>
                <span className="px-1.5 py-0.5 text-[10px] font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded-md uppercase tracking-wider">
                  v14.0 RC
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-medium tracking-wide">
                Revenue Recovery & RegTech Control Center
              </p>
            </div>
          </div>

          {/* Center Navigation Links */}
          <nav className="hidden lg:flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 shadow-xs shadow-indigo-500/10'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 border border-transparent'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-indigo-400' : 'text-slate-500'}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* System Status Indicators */}
          <div className="flex items-center space-x-3">
            <button
              onClick={async () => {
                const btn = document.getElementById('demo-reset-btn');
                if (btn) btn.innerText = 'Resetting...';
                try {
                  const { resetDemoState } = await import('../services/api');
                  await resetDemoState();
                  alert('System Reset Successful! Fresh transaction state initialized.');
                } finally {
                  if (btn) btn.innerText = 'Reset & Run Live';
                }
              }}
              id="demo-reset-btn"
              className="px-3 py-1.5 rounded-xl bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 text-xs font-semibold flex items-center space-x-1.5 transition-all shadow-xs"
              title="Reset system state and re-initialize live transaction processing"
            >
              <RotateCcw className="w-3.5 h-3.5 text-cyan-400" />
              <span>Reset & Run Live</span>
            </button>

            <div className="hidden sm:flex items-center space-x-2 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              <span className="text-[11px] font-semibold text-emerald-400 tracking-wide uppercase">
                OPERATIONAL
              </span>
            </div>
            
            <div className="px-2.5 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-[11px] font-mono text-indigo-300">
              DEMO MODE
            </div>
          </div>

        </div>

        {/* Mobile Navigation Row */}
        <div className="lg:hidden flex overflow-x-auto py-2 space-x-2 no-scrollbar border-t border-slate-800/80">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap ${
                  isActive
                    ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30'
                    : 'text-slate-400 hover:bg-slate-800/40'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>

      </div>
    </header>
  );
}
