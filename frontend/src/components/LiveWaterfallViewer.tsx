'use client';

import React, { useRef, useEffect, useState } from 'react';
import { Layers, ZoomIn, Eye, Activity, Crosshair } from 'lucide-react';

interface Contact {
  contact_id: string;
  classification: string;
  confidence: number;
  bounding_box: {
    x_min: number;
    y_min: number;
    x_max: number;
    y_max: number;
  };
  evidence_graph?: any;
}

interface LiveWaterfallViewerProps {
  frameImage?: string;
  frameWidth?: number;
  frameHeight?: number;
  contacts?: Contact[];
  selectedContactId?: string | null;
  onSelectContact?: (contact: Contact) => void;
  slantRangeM?: number;
  frequencyKhz?: number;
  snrDb?: number;
}

export const LiveWaterfallViewer: React.FC<LiveWaterfallViewerProps> = ({
  frameImage,
  frameWidth = 768,
  frameHeight = 384,
  contacts = [],
  selectedContactId,
  onSelectContact,
  slantRangeM = 50.0,
  frequencyKhz = 900.0,
  snrDb = 24.2
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [colormap, setColormap] = useState<'amber' | 'sepia' | 'jet' | 'navy'>('amber');
  const [showBoxes, setShowBoxes] = useState(true);

  // Draw acoustic frame on canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    if (frameImage) {
      const img = new Image();
      img.onload = () => {
        canvas.width = frameWidth;
        canvas.height = frameHeight;
        ctx.drawImage(img, 0, 0, frameWidth, frameHeight);

        // Apply color tint / filter if desired
        if (colormap === 'amber') {
          ctx.globalCompositeOperation = 'multiply';
          ctx.fillStyle = 'rgba(255, 175, 40, 0.35)';
          ctx.fillRect(0, 0, frameWidth, frameHeight);
          ctx.globalCompositeOperation = 'source-over';
        } else if (colormap === 'sepia') {
          ctx.globalCompositeOperation = 'multiply';
          ctx.fillStyle = 'rgba(215, 160, 95, 0.4)';
          ctx.fillRect(0, 0, frameWidth, frameHeight);
          ctx.globalCompositeOperation = 'source-over';
        } else if (colormap === 'navy') {
          ctx.globalCompositeOperation = 'multiply';
          ctx.fillStyle = 'rgba(60, 140, 240, 0.35)';
          ctx.fillRect(0, 0, frameWidth, frameHeight);
          ctx.globalCompositeOperation = 'source-over';
        }

        // Draw center nadir altitude line
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.25)';
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.moveTo(frameWidth / 2, 0);
        ctx.lineTo(frameWidth / 2, frameHeight);
        ctx.stroke();
        ctx.setLineDash([]);
      };
      img.src = frameImage;
    } else {
      // Default placeholder grid
      canvas.width = frameWidth;
      canvas.height = frameHeight;
      ctx.fillStyle = '#060d17';
      ctx.fillRect(0, 0, frameWidth, frameHeight);

      ctx.strokeStyle = '#0f2238';
      ctx.lineWidth = 1;
      for (let x = 0; x < frameWidth; x += 48) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, frameHeight);
        ctx.stroke();
      }
      for (let y = 0; y < frameHeight; y += 48) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(frameWidth, y);
        ctx.stroke();
      }
    }
  }, [frameImage, frameWidth, frameHeight, colormap]);

  return (
    <div className="relative flex flex-col bg-slate-900/90 border border-slate-800 rounded-xl overflow-hidden shadow-2xl backdrop-blur-md">
      {/* Sonar Header Bar */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-slate-950/80 border-b border-slate-800/80">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400">
            <Activity className="w-4 h-4" />
          </div>
          <div>
            <span className="text-xs font-semibold tracking-wider uppercase text-slate-200">
              Live SSS Waterfall
            </span>
            <span className="ml-2 text-[10px] font-mono text-slate-400">
              {frequencyKhz} kHz • ±{slantRangeM}m Swath
            </span>
          </div>
        </div>

        {/* Colormap & Display Toggles */}
        <div className="flex items-center gap-2">
          <div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-0.5 text-[11px] font-medium">
            <button
              onClick={() => setColormap('amber')}
              className={`px-2 py-0.5 rounded ${colormap === 'amber' ? 'bg-amber-500/20 text-amber-300 font-semibold' : 'text-slate-400 hover:text-slate-200'}`}
            >
              Amber
            </button>
            <button
              onClick={() => setColormap('sepia')}
              className={`px-2 py-0.5 rounded ${colormap === 'sepia' ? 'bg-amber-700/30 text-amber-200 font-semibold' : 'text-slate-400 hover:text-slate-200'}`}
            >
              Copper
            </button>
            <button
              onClick={() => setColormap('navy')}
              className={`px-2 py-0.5 rounded ${colormap === 'navy' ? 'bg-cyan-500/20 text-cyan-300 font-semibold' : 'text-slate-400 hover:text-slate-200'}`}
            >
              Navy
            </button>
          </div>

          <button
            onClick={() => setShowBoxes(!showBoxes)}
            className={`p-1.5 rounded-lg border text-xs flex items-center gap-1 transition ${
              showBoxes 
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' 
                : 'bg-slate-800 border-slate-700 text-slate-400'
            }`}
            title="Toggle AI Bounding Boxes"
          >
            <Crosshair className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Main Waterfall Canvas Area */}
      <div className="relative w-full aspect-[2/1] bg-slate-950 flex items-center justify-center overflow-hidden select-none">
        <canvas
          ref={canvasRef}
          className="w-full h-full object-contain cursor-crosshair"
        />

        {/* Channel Indicators */}
        <div className="absolute top-2 left-3 px-2 py-0.5 rounded bg-black/60 border border-white/10 text-[10px] font-mono text-slate-300 uppercase tracking-wider backdrop-blur-sm pointer-events-none">
          PORT CH ({-slantRangeM}m)
        </div>
        <div className="absolute top-2 right-3 px-2 py-0.5 rounded bg-black/60 border border-white/10 text-[10px] font-mono text-slate-300 uppercase tracking-wider backdrop-blur-sm pointer-events-none">
          STARBOARD CH (+{slantRangeM}m)
        </div>
        <div className="absolute top-2 left-1/2 -translate-x-1/2 px-2 py-0.5 rounded bg-black/60 border border-white/10 text-[9px] font-mono text-amber-400/90 tracking-widest backdrop-blur-sm pointer-events-none">
          NADIR
        </div>

        {/* Bounding Box Overlays */}
        {showBoxes && contacts.map((c) => {
          const isSelected = selectedContactId === c.contact_id;
          const leftPct = (c.bounding_box.x_min / frameWidth) * 100;
          const topPct = (c.bounding_box.y_min / frameHeight) * 100;
          const widthPct = ((c.bounding_box.x_max - c.bounding_box.x_min) / frameWidth) * 100;
          const heightPct = ((c.bounding_box.y_max - c.bounding_box.y_min) / frameHeight) * 100;

          const isAnthropogenic = c.classification.toLowerCase() !== 'natural_seabed' && c.classification.toLowerCase() !== 'natural_boulder';
          const borderColor = isSelected 
            ? 'border-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.6)]' 
            : isAnthropogenic 
              ? 'border-emerald-400/90 shadow-[0_0_8px_rgba(52,211,153,0.3)]' 
              : 'border-amber-400/80';

          return (
            <div
              key={c.contact_id}
              onClick={() => onSelectContact && onSelectContact(c)}
              style={{
                left: `${leftPct}%`,
                top: `${topPct}%`,
                width: `${Math.max(widthPct, 4)}%`,
                height: `${Math.max(heightPct, 6)}%`
              }}
              className={`absolute border-2 rounded transition-all cursor-pointer hover:scale-105 z-10 ${borderColor} ${isSelected ? 'bg-cyan-500/20' : 'bg-black/20 hover:bg-white/10'}`}
            >
              <div className="absolute -top-6 left-0 flex items-center gap-1 px-1.5 py-0.5 rounded bg-slate-950/90 border border-slate-700/80 text-[10px] font-mono whitespace-nowrap backdrop-blur-md">
                <span className={isAnthropogenic ? 'text-emerald-400 font-bold' : 'text-amber-400'}>
                  {c.classification.replace('_', ' ')}
                </span>
                <span className="text-slate-400">
                  {(c.confidence * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          );
        })}

        {/* Quality Control Watermark */}
        <div className="absolute bottom-2 left-3 flex items-center gap-2 px-2.5 py-1 rounded-md bg-slate-950/80 border border-slate-800 text-[11px] font-mono text-slate-400 backdrop-blur-sm pointer-events-none">
          <span>SNR: <strong className={snrDb > 15 ? 'text-emerald-400' : 'text-amber-400'}>{snrDb.toFixed(1)} dB</strong></span>
          <span className="text-slate-600">|</span>
          <span>Detections: <strong className="text-slate-200">{contacts.length}</strong></span>
        </div>
      </div>
    </div>
  );
};
