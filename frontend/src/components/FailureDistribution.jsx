import React from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from 'recharts';

export default function FailureDistribution({ distribution }) {
  if (!distribution) return null;

  const COLORS = ['#6366f1', '#38bdf8', '#34d399', '#fbbf24', '#f43f5e', '#94a3b8'];

  const formattedData = distribution.map((item) => ({
    name: item.category.replace('_', ' '),
    rawName: item.category,
    count: item.count,
    pct: item.pct,
  }));

  return (
    <div className="glass-card p-5 rounded-xl flex flex-col justify-between">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-200">Failure Category Distribution</h3>
          <p className="text-xs text-slate-400">Phase 10 deterministic failure taxonomy classification</p>
        </div>
        <span className="px-2 py-0.5 text-[10px] font-mono font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded-md">
          500 CASES
        </span>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={formattedData} layout="vertical" margin={{ top: 5, right: 20, left: 40, bottom: 5 }}>
            <XAxis type="number" stroke="#64748b" fontSize={11} tickLine={false} />
            <YAxis type="category" dataKey="name" stroke="#94a3b8" fontSize={10} tickLine={false} width={150} />
            <Tooltip
              contentStyle={{ background: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px', color: '#f8fafc' }}
              formatter={(value, name, props) => [`${value} cases (${props.payload.pct}%)`, 'Volume']}
            />
            <Bar dataKey="count" radius={[0, 4, 4, 0]}>
              {formattedData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Grid Legend */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mt-4 pt-3 border-t border-slate-800 text-[11px]">
        {distribution.map((item, idx) => (
          <div key={item.category} className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-xs shrink-0" style={{ backgroundColor: COLORS[idx % COLORS.length] }} />
            <span className="text-slate-300 font-mono truncate">{item.category}</span>
            <span className="text-slate-500 font-bold ml-auto">{item.count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
