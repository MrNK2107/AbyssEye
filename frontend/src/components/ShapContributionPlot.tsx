'use client';

import React from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell, ReferenceLine } from 'recharts';
import { ShapFeatureImpact } from '@/types/contact';

interface ShapPlotProps {
  features: ShapFeatureImpact[];
}

export const ShapContributionPlot: React.FC<ShapPlotProps> = ({ features }) => {
  if (!features || features.length === 0) {
    return (
      <div className="w-full h-40 bg-ocean-950/80 rounded-xl p-3 border border-ocean-800 flex items-center justify-center text-xs text-slate-500">
        No SHAP attribution data available
      </div>
    );
  }

  const chartData = features.map(f => ({
    name: f.feature.replace(/_/g, ' '),
    impact: f.shap_impact,
    val: f.value
  }));

  return (
    <div className="w-full h-44 bg-ocean-950/80 rounded-xl p-3 border border-ocean-800">
      <div className="flex items-center justify-between mb-1.5 px-1">
        <span className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider">
          TreeSHAP Feature Attribution (Local Evidence Weights)
        </span>
        <div className="flex items-center gap-2 text-[10px]">
          <span className="text-emerald-400 font-medium">+ Debris</span>
          <span className="text-rose-400 font-medium">- Natural</span>
        </div>
      </div>
      <ResponsiveContainer width="100%" height="82%">
        <BarChart
          layout="vertical"
          data={chartData}
          margin={{ top: 5, right: 20, left: 35, bottom: 0 }}
        >
          <XAxis type="number" stroke="#475569" tick={{ fontSize: 9, fill: '#94a3b8' }} />
          <YAxis
            type="category"
            dataKey="name"
            stroke="#475569"
            tick={{ fontSize: 9, fill: '#cbd5e1' }}
            width={85}
          />
          <Tooltip
            contentStyle={{ backgroundColor: '#071328', borderColor: '#1e528e', fontSize: '11px', borderRadius: '8px' }}
            formatter={(value: any) => [`${value > 0 ? '+' : ''}${value}`, 'SHAP Impact']}
          />
          <ReferenceLine x={0} stroke="#475569" />
          <Bar dataKey="impact" radius={[0, 4, 4, 0]}>
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.impact >= 0 ? '#10b981' : '#f43f5e'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
