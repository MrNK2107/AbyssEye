'use client';

import React, { useRef, useEffect, useState } from 'react';
import { Activity, Crosshair, SplitSquareVertical, SlidersHorizontal, Sparkles } from 'lucide-react';

interface Contact {
  contact_id: string;
  classification?: string;
  confidence?: number;
  bounding_box?: {
    x_min: number;
    y_min: number;
    x_max: number;
    y_max: number;
  };
  bbox?: [number, number, number, number] | number[];
  target_type_hint?: string;
  triage_state?: string;
  fusion_decision?: any;
  evidence_graph?: any;
}

interface LiveWaterfallViewerProps {
  frameImage?: string;
  rawFrameImage?: string;
  preprocessedFrameImage?: string;
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
  rawFrameImage,
  preprocessedFrameImage,
  frameWidth = 768,
  frameHeight = 384,
  contacts = [],
  selectedContactId,
  onSelectContact,
  slantRangeM = 50.0,
  frequencyKhz = 410.0,
  snrDb = 24.2
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [viewMode, setViewMode] = useState<'preprocessed' | 'raw' | 'split'>('preprocessed');
  const [colormap, setColormap] = useState<'amber' | 'sepia' | 'navy'>('amber');
  const [showBoxes, setShowBoxes] = useState(true);

  // Draw acoustic frame on canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const activeImageSrc = 
      viewMode === 'raw' 
        ? (rawFrameImage || frameImage) 
        : (preprocessedFrameImage || frameImage);

    if (activeImageSrc) {
      const img = new Image();
      img.onload = () => {
        canvas.width = frameWidth;
        canvas.height = frameHeight;

        if (viewMode === 'split' && rawFrameImage && preprocessedFrameImage) {
          // Draw split screen: Left half Raw, Right half Preprocessed
          const rawImg = new Image();
          rawImg.onload = () => {
            // Draw left half raw
            ctx.drawImage(rawImg, 0, 0, frameWidth / 2, frameHeight, 0, 0, frameWidth / 2, frameHeight);
            // Draw right half preprocessed
            ctx.drawImage(img, frameWidth / 2, 0, frameWidth / 2, frameHeight, frameWidth / 2, 0, frameWidth / 2, frameHeight);
            
            // Split divider line
            ctx.strokeStyle = '#06b6d4';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(frameWidth / 2, 0);
            ctx.lineTo(frameWidth / 2, frameHeight);
            ctx.stroke();
          };
          rawImg.src = rawFrameImage;
        } else {
          ctx.drawImage(img, 0, 0, frameWidth, frameHeight);
        }

        // Apply Colormap Tint
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

        // Center Nadir Altitude Line
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.25)';
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.moveTo(frameWidth / 2, 0);
        ctx.lineTo(frameWidth / 2, frameHeight);
        ctx.stroke();
        ctx.setLineDash([]);
      };
      img.src = activeImageSrc;
    } else {
      canvas.width = frameWidth;
      canvas.height = frameHeight;
      ctx.fillStyle = '#060d17';
      ctx.fillRect(0, 0, frameWidth, frameHeight);
    }
  }, [frameImage, rawFrameImage, preprocessedFrameImage, frameWidth, frameHeight, viewMode, colormap]);

  return (
    <div className="relative flex flex-col bg-slate-900/90 border border-slate-800 rounded-xl overflow-hidden shadow-2xl backdrop-blur-md">
      {/* Sonar Header Bar */}
      <div className="flex flex-wrap items-center justify-between px-4 py-2.5 bg-slate-950/90 border-b border-slate-800/80 gap-2">
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

        {/* View Mode & Colormap Selectors */}
        <div className="flex items-center gap-2">
          {/* Signal Processing View Mode */}
          <div className="flex items-center bg-slate-950 border border-slate-800 rounded-lg p-0.5 text-[11px] font-mono">
            <button
              onClick={() => setViewMode('preprocessed')}
              className={`flex items-center gap-1 px-2 py-0.5 rounded transition ${viewMode === 'preprocessed' ? 'bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-500/40' : 'text-slate-400 hover:text-slate-200'}`}
              title="Lee Despeckled + CLAHE Enhanced"
            >
              <Sparkles className="w-3 h-3 text-cyan-400" />
              <span>Enhanced</span>
            </button>
            <button
              onClick={() => setViewMode('raw')}
              className={`px-2 py-0.5 rounded transition ${viewMode === 'raw' ? 'bg-slate-800 text-slate-200 font-bold' : 'text-slate-400 hover:text-slate-200'}`}
              title="Raw Sonar Backscatter"
            >
              Raw
            </button>
            <button
              onClick={() => setViewMode('split')}
              className={`flex items-center gap-1 px-2 py-0.5 rounded transition ${viewMode === 'split' ? 'bg-purple-500/20 text-purple-300 font-bold border border-purple-500/40' : 'text-slate-400 hover:text-slate-200'}`}
              title="Split View (Raw vs Enhanced)"
            >
              <SplitSquareVertical className="w-3 h-3" />
              <span>Split</span>
            </button>
          </div>

          {/* Colormap Selector */}
          <div className="flex items-center bg-slate-950 border border-slate-800 rounded-lg p-0.5 text-[11px] font-medium">
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

          {/* Bounding Box Toggle */}
          <button
            onClick={() => setShowBoxes(!showBoxes)}
            className={`p-1.5 rounded-lg border text-xs flex items-center gap-1 transition ${
              showBoxes 
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' 
                : 'bg-slate-800 border-slate-700 text-slate-400'
            }`}
            title="Toggle AI Detection Bounding Boxes"
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
          {viewMode === 'split' ? 'RAW ◄ | ► ENHANCED' : 'NADIR'}
        </div>

        {/* Bounding Box Overlays */}
        {showBoxes && contacts.map((c) => {
          if (!c) return null;
          const isSelected = selectedContactId === c.contact_id;
          
          let xMin = 100;
          let yMin = 100;
          let xMax = 200;
          let yMax = 200;

          if (c.bounding_box && typeof c.bounding_box.x_min === 'number') {
            xMin = c.bounding_box.x_min;
            yMin = c.bounding_box.y_min;
            xMax = c.bounding_box.x_max;
            yMax = c.bounding_box.y_max;
          } else if (Array.isArray(c.bbox) && c.bbox.length === 4) {
            const [b0, b1, b2, b3] = c.bbox;
            // Handle [x, y, w, h] vs [xmin, ymin, xmax, ymax]
            if (b2 > b0 && b3 > b1 && b2 <= frameWidth && b3 <= frameHeight) {
              xMin = b0;
              yMin = b1;
              xMax = b2;
              yMax = b3;
            } else {
              xMin = b0;
              yMin = b1;
              xMax = b0 + b2;
              yMax = b1 + b3;
            }
          }

          const leftPct = (xMin / frameWidth) * 100;
          const topPct = (yMin / frameHeight) * 100;
          const widthPct = ((xMax - xMin) / frameWidth) * 100;
          const heightPct = ((yMax - yMin) / frameHeight) * 100;

          const rawClass = c.classification || c.target_type_hint || c.triage_state || 'TARGET';
          const isAnthropogenic = rawClass.toLowerCase() !== 'natural_seabed' && rawClass.toLowerCase() !== 'natural_boulder';
          const confidenceVal = c.confidence ?? c.fusion_decision?.calibrated_probabilities?.p_anthropogenic ?? c.evidence_graph?.discovery?.confidence ?? 0.85;

          const borderColor = isSelected 
            ? 'border-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.7)]' 
            : isAnthropogenic 
              ? 'border-emerald-400/90 shadow-[0_0_8px_rgba(52,211,153,0.3)]' 
              : 'border-amber-400/80';

          return (
            <div
              key={c.contact_id || Math.random().toString()}
              onClick={() => onSelectContact && onSelectContact(c)}
              style={{
                left: `${Math.max(0, Math.min(leftPct, 95))}%`,
                top: `${Math.max(0, Math.min(topPct, 95))}%`,
                width: `${Math.max(widthPct, 4)}%`,
                height: `${Math.max(heightPct, 6)}%`
              }}
              className={`absolute border-2 rounded transition-all cursor-pointer hover:scale-105 z-10 ${borderColor} ${isSelected ? 'bg-cyan-500/20' : 'bg-black/20 hover:bg-white/10'}`}
            >
              <div className="absolute -top-6 left-0 flex items-center gap-1 px-1.5 py-0.5 rounded bg-slate-950/90 border border-slate-700/80 text-[10px] font-mono whitespace-nowrap backdrop-blur-md">
                <span className={isAnthropogenic ? 'text-emerald-400 font-bold' : 'text-amber-400'}>
                  {rawClass.replace(/_/g, ' ')}
                </span>
                <span className="text-slate-400">
                  {(confidenceVal * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          );
        })}

        {/* Live Filter Engine Watermark */}
        <div className="absolute bottom-2 left-3 flex items-center gap-2 px-2.5 py-1 rounded-md bg-slate-950/80 border border-slate-800 text-[10px] font-mono text-slate-400 backdrop-blur-sm pointer-events-none">
          <span className="text-cyan-400 font-semibold">
            {viewMode === 'preprocessed' ? 'DSP: [Lee Despeckle 5x5 + CLAHE 2.5]' : viewMode === 'raw' ? 'DSP: [Raw Backscatter]' : 'DSP: [Dual-Split Mode]'}
          </span>
          <span className="text-slate-600">|</span>
          <span>SNR: <strong className={snrDb > 15 ? 'text-emerald-400' : 'text-amber-400'}>{snrDb.toFixed(1)} dB</strong></span>
        </div>
      </div>
    </div>
  );
};
