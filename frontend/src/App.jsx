import React, { useState } from 'react';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import RecoveryTable from './components/RecoveryTable';
import AIDecisions from './pages/AIDecisions';
import GovernancePanel from './components/GovernancePanel';
import SimulationPanel from './components/SimulationPanel';
import AuditPanel from './components/AuditPanel';
import Health from './pages/Health';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans antialiased">
      
      {/* Sticky Header Navigation */}
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Content Body */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'overview' && <Dashboard setActiveTab={setActiveTab} />}
        {activeTab === 'cases' && <RecoveryTable />}
        {activeTab === 'ai' && <AIDecisions />}
        {activeTab === 'governance' && <GovernancePanel />}
        {activeTab === 'simulation' && <SimulationPanel />}
        {activeTab === 'audit' && <AuditPanel />}
        {activeTab === 'health' && <Health />}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-6 text-center text-xs text-slate-500 glass-panel mt-auto">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>RecoverAI Command Center — Revenue Recovery Engine & RegTech Firewall</span>
          <span className="font-mono text-[11px] text-slate-400">Environment: DEMO MODE (Read-Only Safety Active)</span>
        </div>
      </footer>

    </div>
  );
}
