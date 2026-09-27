'use client';

import React from 'react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, ReferenceLine } from 'recharts';

interface ProfilePlotProps {
  beamProfile?: Array<{
    sample_idx: number;
    range_offset_m: number;
    intensity: number;
    region: string;
  }>;
  peakIntensity?: number;
  shadowLengthM?: number;
  hasShadow?: boolean;
}

export const AcousticProfilePlot: React.FC<ProfilePlotProps> = ({
  beamProfile,
  peakIntensity = 220,
  shadowLengthM = 5.0,
  hasShadow = true
}) => {
  let chartData: Array<{ range: string; intensity: number; region?: string }> = [];

  if (beamProfile && beamProfile.length > 0) {
    chartData = beamProfile.map(item => ({
      range: `${item.range_offset_m >= 0 ? '+' : ''}${item.range_offset_m}m`,
      intensity: item.intensity,
      region: item.region.replace('_', ' ')
    }));
  } else {
    // Fallback derived strictly from physics metrics
    const totalPoints = 35;
    for (let i = 0; i < totalPoints; i++) {
      const rangeM = ((i - 10) * 0.4).toFixed(1);
      let intensity = 110;
      let region = "AMBIENT SEABED";

      if (i >= 8 && i <= 12) {
        intensity = peakIntensity - Math.abs(i - 10) * 18;
        region = "HIGHLIGHT PEAK";
      } else if (hasShadow && i > 12 && i <= 12 + Math.round(shadowLengthM / 0.4)) {
        intensity = 18;
        region = "ACOUSTIC SHADOW";
      }

      chartData.push({
        range: `${parseFloat(rangeM) >= 0 ? '+' : ''}${rangeM}m`,
        intensity: Math.round(Math.max(0, Math.min(255, intensity))),
        region
      });
    }
  }

  return (
    <div className="w-full h-44 bg-ocean-950/90 rounded-xl p-3 border border-ocean-800">
      <div className="flex items-center justify-between mb-1.5 px-1">
        <span className="text-[11px] font-semibold text-slate-200 uppercase tracking-wider font-mono flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-cyan-400" />
          1D Acoustic Ray Intensity Cross-Section
        </span>
        <span className="text-[10px] text-cyan-400 font-mono">
          Nadir ➔ Target ➔ Shadow
        </span>
      </div>
      <ResponsiveContainer width="100%" height="82%">
        <AreaChart data={chartData} margin={{ top: 5, right: 10, left: -25, bottom: 0 }}>
          <defs>
            <linearGradient id="intensityGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.0} />
            </linearGradient>
          </defs>
          <XAxis dataKey="range" stroke="#475569" tick={{ fontSize: 9, fill: '#94a3b8' }} interval={4} />
          <YAxis domain={[0, 255]} stroke="#475569" tick={{ fontSize: 9, fill: '#94a3b8' }} />
          <Tooltip
            contentStyle={{ backgroundColor: '#071328', borderColor: '#1e528e', fontSize: '11px', borderRadius: '8px', color: '#e2e8f0' }}
            formatter={(value: any, name: any, item: any) => [
              `${value} DN (${item?.payload?.region || ''})`,
              'Acoustic Backscatter'
            ]}
          />
          <ReferenceLine y={110} stroke="#334155" strokeDasharray="3 3" label={{ value: 'Seabed Baseline', fill: '#64748b', fontSize: 9 }} />
          <Area
            type="monotone"
            dataKey="intensity"
            stroke="#06b6d4"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#intensityGradient)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};
