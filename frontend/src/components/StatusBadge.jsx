import React from 'react';

export default function StatusBadge({ type, value }) {
  if (type === 'opa') {
    const isAllow = value === 'ALLOW' || value === 'ALLOWED' || value === true;
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider ${
        isAllow 
          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
          : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
      }`}>
        {isAllow ? 'ALLOW' : 'DENY'}
      </span>
    );
  }

  // State machine status badge
  let badgeStyle = 'bg-slate-700/40 text-slate-300 border-slate-600/30';
  if (value === 'RECOVERED') {
    badgeStyle = 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30 shadow-xs shadow-emerald-500/10';
  } else if (value === 'AWAITING_SETTLEMENT') {
    badgeStyle = 'bg-amber-500/15 text-amber-300 border-amber-500/30 animate-pulse';
  } else if (value === 'ACTION_EXECUTED') {
    badgeStyle = 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30';
  } else if (value === 'BLOCKED') {
    badgeStyle = 'bg-rose-500/15 text-rose-300 border-rose-500/30';
  } else if (value === 'DIAGNOSED' || value === 'DETECTED') {
    badgeStyle = 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30';
  }

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-mono font-medium border ${badgeStyle}`}>
      {value}
    </span>
  );
}
