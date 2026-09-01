import React, { useState, useEffect } from 'react';
import { Search, Filter, Eye, X, ChevronLeft, ChevronRight } from 'lucide-react';
import StatusBadge from './StatusBadge';
import RecoveryTimeline from './RecoveryTimeline';
import { fetchDemoCases, getSyntheticRecoveryCases } from '../services/api';

export default function RecoveryTable() {
  const [cases, setCases] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCases, setTotalCases] = useState(0);
  const [selectedCase, setSelectedCase] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadCases = async () => {
    setLoading(true);
    try {
      const res = await fetchDemoCases(page, pageSize, searchTerm, statusFilter);
      if (res && res.items && res.items.length > 0) {
        setCases(res.items);
        setTotalPages(res.total_pages || 1);
        setTotalCases(res.total || res.items.length);
      } else {
        // Fallback to synthetic cases if empty interactive demo
        const fallback = getSyntheticRecoveryCases();
        const filtered = fallback.filter((c) => {
          const matchSearch = !searchTerm || c.case_id.toLowerCase().includes(searchTerm.toLowerCase()) || c.payment_id.toLowerCase().includes(searchTerm.toLowerCase());
          const matchStatus = statusFilter === 'ALL' || c.current_state === statusFilter;
          return matchSearch && matchStatus;
        });
        setCases(filtered);
        setTotalPages(1);
        setTotalCases(filtered.length);
      }
    } catch (err) {
      setCases(getSyntheticRecoveryCases());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCases();
  }, [page, searchTerm, statusFilter]);

  return (
    <div className="space-y-6">
      
      {/* Search and Filters Bar */}
      <div className="glass-card p-4 rounded-xl flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search Case ID, Payment ID..."
            value={searchTerm}
            onChange={(e) => { setSearchTerm(e.target.value); setPage(1); }}
            className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
        </div>

        <div className="flex items-center space-x-2 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-slate-500" />
          <span className="text-xs text-slate-400">Filter Status:</span>
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            className="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="ALL">All States</option>
            <option value="AWAITING_SETTLEMENT">AWAITING_SETTLEMENT</option>
            <option value="RECOVERED">RECOVERED</option>
            <option value="ACTION_EXECUTED">ACTION_EXECUTED</option>
            <option value="BLOCKED">BLOCKED</option>
          </select>
        </div>
      </div>

      {/* Table Container */}
      <div className="glass-card rounded-xl overflow-hidden border border-slate-800">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/80 text-slate-400 uppercase font-mono text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Case ID</th>
                <th className="py-3 px-4">Payment ID</th>
                <th className="py-3 px-4">Failure Category</th>
                <th className="py-3 px-4 text-right">Amount (₹)</th>
                <th className="py-3 px-4 text-center">AI Confidence</th>
                <th className="py-3 px-4 text-center">OPA Decision</th>
                <th className="py-3 px-4 text-center">Current State</th>
                <th className="py-3 px-4 text-center">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {cases.map((c) => (
                <tr key={c.case_id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-3 px-4 font-mono font-bold text-indigo-300">{c.case_id}</td>
                  <td className="py-3 px-4 font-mono text-slate-400">{c.payment_id}</td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 rounded-sm bg-slate-800 text-slate-300 font-mono text-[11px]">
                      {c.failure_category}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right font-mono font-semibold text-slate-200">
                    ₹{((c.amount_paise || 0) / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="py-3 px-4 text-center font-mono font-bold text-amber-400">
                    {((c.ai_confidence || 0) * 100).toFixed(0)}%
                  </td>
                  <td className="py-3 px-4 text-center">
                    <StatusBadge type="opa" value={c.opa_decision} />
                  </td>
                  <td className="py-3 px-4 text-center">
                    <StatusBadge type="state" value={c.current_state} />
                  </td>
                  <td className="py-3 px-4 text-center">
                    <button
                      onClick={() => setSelectedCase(c)}
                      className="px-2.5 py-1 rounded-lg bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 hover:bg-indigo-600/30 font-medium inline-flex items-center space-x-1"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>Lifecycle</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        <div className="px-4 py-3 bg-slate-900/60 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400 font-mono">
          <div>
            Showing <span className="font-bold text-slate-200">{cases.length}</span> of <span className="font-bold text-slate-200">{totalCases}</span> total cases
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-300 flex items-center space-x-1"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
              <span>Previous</span>
            </button>
            <span className="px-2 text-slate-300 font-bold">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-300 flex items-center space-x-1"
            >
              <span>Next</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Case Lifecycle Modal Drawer */}
      {selectedCase && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="glass-panel w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl p-6 border border-slate-800 relative shadow-2xl">
            
            <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-6">
              <div>
                <span className="text-[10px] font-mono text-indigo-400 uppercase tracking-widest block">RECOVERY CASE LIFECYCLE</span>
                <h3 className="text-lg font-bold text-slate-100 font-mono">{selectedCase.case_id} — {selectedCase.payment_id}</h3>
              </div>
              <button
                onClick={() => setSelectedCase(null)}
                className="p-1 rounded-lg bg-slate-800 text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <RecoveryTimeline selectedCase={selectedCase} />

            <div className="mt-6 pt-4 border-t border-slate-800 flex justify-end">
              <button
                onClick={() => setSelectedCase(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 hover:bg-slate-700 text-xs font-semibold"
              >
                Close View
              </button>
            </div>

          </div>
        </div>
      )}

    </div>
  );
}
