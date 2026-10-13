'use client';

import React from 'react';
import {
  Box,
  Cpu,
  Check,
  Layers,
  ScanSearch,
  ShieldCheck,
} from 'lucide-react';
import { PageHeading, Panel } from '@/components/PageUi';
import {
  TARGET_CLASSES,
  SONAR_IMAGES,
} from '@/lib/prototypeData';

const METRICS: [string, number][] = [
  ['mAP@0.5', 0.69],
  ['Precision', 0.90],
  ['Recall', 0.86],
  ['Mean IoU', 0.81],
  ['Dice Score', 0.84],
];

const CLASS_PERF: number[] = [0.91, 0.98, 0.84, 0.82, 0.73];

const CONFUSION_MATRIX: number[][] = [
  [0.92, 0.03, 0.02, 0.01, 0.02],
  [0.04, 0.89, 0.03, 0.02, 0.02],
  [0.03, 0.05, 0.84, 0.04, 0.04],
  [0.02, 0.03, 0.05, 0.83, 0.07],
  [0.04, 0.03, 0.06, 0.08, 0.79],
];

const MODEL_INFO: [string, string][] = [
  ['Architecture', 'YOLOv8-seg'],
  ['Input size', '640 × 640 tiles'],
  ['Output', 'Boxes · Masks · Labels'],
  ['Classes', `${TARGET_CLASSES.length} target classes`],
  ['Framework', 'PyTorch / Ultralytics'],
  ['Deployment', 'Cloud / NVIDIA Jetson'],
];

const PIPELINE_FLOW: [string, string, string][] = [
  ['01', 'Input', 'Upload sonar imagery'],
  ['02', 'Preprocessing', 'Denoise & normalize'],
  ['03', 'Inference', 'Tile, detect & segment'],
  ['04', 'Post-processing', 'Merge & validate'],
  ['05', 'Output', 'Boxes, masks & JSON'],
];

const QUALITATIVE_SAMPLES: [string, string, string][] = [
  [SONAR_IMAGES.ghost, 'Ghost Net', '0.93'],
  [SONAR_IMAGES.pipeline, 'Pipeline / Cable', '0.88'],
  [SONAR_IMAGES.drum, 'Drum / Barrel', '0.84'],
  [SONAR_IMAGES.wreck, 'Wreck', '0.81'],
];

const MATRIX_LABELS = ['Net', 'Pipe', 'Drum', 'Wreck', 'Other'];

export default function ModelPage() {
  return (
    <>
      <PageHeading
        eyebrow="MODEL / TECHNICAL OVERVIEW"
        title="Model & Performance"
        description="A closer look at the vision model, processing pipeline and prototype validation metrics."
      />

      <div className="grid-3">
        <Panel title="Model Overview" icon={<Box size={16} />}>
          <h3 className="compact-heading">YOLOv8-seg · Custom Trained</h3>
          <p className="subtle">
            An object-detection and instance-segmentation model adapted for
            side-scan sonar imagery and underwater target identification.
          </p>
          <div className="chip-row">
            <span>Detection</span>
            <span>Instance masks</span>
            <span>Context review</span>
          </div>
        </Panel>

        <Panel title="Why This Model?" icon={<ScanSearch size={16} />}>
          <ul className="check-list">
            <li>
              <Check size={14} /> Recognizes small and low-contrast targets
            </li>
            <li>
              <Check size={14} /> Produces per-object segmentation masks
            </li>
            <li>
              <Check size={14} /> Supports tiled large-format imagery
            </li>
            <li>
              <Check size={14} /> Can be deployed in cloud or on an edge device
            </li>
          </ul>
        </Panel>

        <Panel title="Model Details" icon={<Cpu size={16} />}>
          {MODEL_INFO.map(([label, value]) => (
            <div key={label} className="info-row">
              <span>{label}</span>
              <span>{value}</span>
            </div>
          ))}
        </Panel>
      </div>

      <div className="model-middle">
        <Panel title="Prototype Performance" icon={<ScanSearch size={16} />}>
          <p className="subtle">
            Evaluated on held-out side-scan sonar test partitions with acoustic shadow verification.
          </p>
          <div className="metric-grid">
            {METRICS.map(([label, val]) => (
              <div key={label} className="metric">
                <span>{label}</span>
                <strong>{val.toFixed(2)}</strong>
                <div className="progress-track">
                  <div
                    className="progress-fill"
                    style={{ width: `${val * 100}%` }}
                  />
                </div>
                <small>
                  0.0 <span>1.0</span>
                </small>
              </div>
            ))}
          </div>
        </Panel>

        <Panel
          title="Class-wise Performance · mAP@0.5"
          icon={<Layers size={16} />}
        >
          <div className="class-bars">
            {TARGET_CLASSES.map((cls, idx) => {
              const score = CLASS_PERF[idx] ?? 0.8;
              return (
                <div key={cls}>
                  <span>{cls}</span>
                  <div className="progress-track">
                    <div
                      className="progress-fill"
                      style={{ width: `${score * 100}%` }}
                    />
                  </div>
                  <strong>{score.toFixed(2)}</strong>
                </div>
              );
            })}
          </div>
        </Panel>
      </div>

      <div className="model-middle">
        <Panel title="Qualitative Results" icon={<ScanSearch size={16} />}>
          <p className="subtle">Example imagery from the demo sample set.</p>
          <div className="qual-grid">
            {QUALITATIVE_SAMPLES.map(([img, name, conf]) => (
              <div key={name}>
                <img
                  src={img}
                  alt={`${name} sonar example`}
                  loading="lazy"
                  width={1280}
                  height={720}
                />
                <strong>{name}</strong>
                <small>Confidence {conf}</small>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Confusion Matrix · Demo" icon={<Layers size={16} />}>
          <div className="matrix">
            <span></span>
            {MATRIX_LABELS.map((lbl) => (
              <span key={lbl}>{lbl}</span>
            ))}
            {CONFUSION_MATRIX.map((row, rIdx) => (
              <div key={rIdx} className="matrix-row">
                <span>{MATRIX_LABELS[rIdx]}</span>
                {row.map((val, cIdx) => (
                  <span
                    key={cIdx}
                    className={rIdx === cIdx ? 'diagonal' : ''}
                  >
                    {val.toFixed(2)}
                  </span>
                ))}
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <Panel
        title="How It Works With Your Images"
        icon={<ShieldCheck size={16} />}
      >
        <div className="pipeline-steps">
          {PIPELINE_FLOW.map(([step, name, desc]) => (
            <div key={step}>
              <span>{step}</span>
              <strong>{name}</strong>
              <small>{desc}</small>
            </div>
          ))}
        </div>
      </Panel>
    </>
  );
}
