import React from 'react';

export default function MetricCard({ title, value, subtext, icon: Icon, color = 'indigo', accent }) {
  const colorMap = {
    indigo: 'text-indigo-400 border-indigo-500/20 bg-indigo-500/10',
    emerald: 'text-emerald-400 border-emerald-500/20 bg-emerald-500/10',
    amber: 'text-amber-400 border-amber-500/20 bg-amber-500/10',
    rose: 'text-rose-400 border-rose-500/20 bg-rose-500/10',
    cyan: 'text-cyan-400 border-cyan-500/20 bg-cyan-500/10',
  };

  return (
    <div className="glass-card glass-card-hover p-5 rounded-xl flex flex-col justify-between relative overflow-hidden">
      {accent && (
        <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-bl from-indigo-500/10 to-transparent pointer-events-none rounded-bl-full" />
      )}
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">{title}</span>
        {Icon && (
          <div className={`p-2 rounded-lg border ${colorMap[color] || colorMap.indigo}`}>
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>

      <div>
        <div className="text-2xl font-bold text-slate-100 font-mono tracking-tight">{value}</div>
        {subtext && <div className="text-xs text-slate-400 mt-1 font-sans">{subtext}</div>}
      </div>
    </div>
  );
}
