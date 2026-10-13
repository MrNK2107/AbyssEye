'use client';

import React from 'react';
import Link from 'next/link';
import {
  ArrowRight,
  BookOpen,
  FileUp,
  Layers,
  ScanSearch,
  ShieldCheck,
  Server,
  Code2,
  LockKeyhole,
} from 'lucide-react';
import { PageHeading, Panel } from '@/components/PageUi';
import { PIPELINE_STAGES, TARGET_CLASSES } from '@/lib/prototypeData';

const JSON_EXAMPLE = `{
  "analysis_id": "AN-...",
  "status": "completed",
  "detections": [{
    "class_name": "Ghost Net",
    "confidence": 0.93,
    "bbox": [13, 18, 32, 57],
    "mask": [[15, 21], ...],
    "validated": true,
    "location": null
  }]
}`;

export default function DocumentationPage() {
  return (
    <>
      <PageHeading
        eyebrow="PLATFORM GUIDE"
        title="Documentation"
        description="Inputs, analysis workflow and integration details for the ABYSSEYE prototype."
      />

      <div className="docs-intro">
        <BookOpen size={24} />
        <div>
          <strong>Quick start</strong>
          <p>
            Choose a sample or upload a sonar image, adjust the confidence
            threshold, run an analysis, then inspect detections and export a
            report.
          </p>
        </div>
        <Link
          href="/analyze"
          className="inline-flex items-center justify-center gap-1.5 whitespace-nowrap text-xs font-medium cursor-pointer transition-colors bg-primary text-primary-foreground shadow hover:bg-primary/90 h-8 rounded-md px-3"
        >
          Open Analyze <ArrowRight size={14} />
        </Link>
      </div>

      <div className="grid-2 docs-grid">
        <Panel title="Supported Inputs" icon={<FileUp size={16} />}>
          <p className="subtle">
            For the local prototype, image uploads can be previewed in the
            browser. Raw sonar formats require a decoder on the future server.
          </p>
          <div className="doc-rows">
            <div>
              <strong>Image</strong>
              <span>PNG, JPG/JPEG, TIFF · up to 500 MB</span>
            </div>
            <div>
              <strong>Raw sonar</strong>
              <span>XTF, JSF · planned server-side decoding</span>
            </div>
            <div>
              <strong>Navigation</strong>
              <span>CSV · timestamp, latitude, longitude, heading</span>
            </div>
          </div>
        </Panel>

        <Panel title="Analysis Workflow" icon={<Layers size={16} />}>
          <ol className="doc-stages">
            {PIPELINE_STAGES.map((stage, idx) => (
              <li key={stage}>
                <span>{String(idx + 1).padStart(2, '0')}</span>
                {stage}
              </li>
            ))}
          </ol>
        </Panel>

        <Panel title="Model & Outputs" icon={<ScanSearch size={16} />}>
          <p className="subtle">
            The planned inference model is a custom-trained YOLOv8-seg network
            for detection and instance segmentation.
          </p>
          <div className="chip-row">
            {TARGET_CLASSES.map((cls) => (
              <span key={cls}>{cls}</span>
            ))}
          </div>
          <p className="subtle">
            Outputs include class labels, confidence scores, normalized
            bounding boxes, segmentation polygons, validation state and optional
            coordinates.
          </p>
        </Panel>

        <Panel title="Reading a Result" icon={<ShieldCheck size={16} />}>
          <p className="subtle">
            Select a target in the image or detection list to inspect its
            confidence and details. Switch among detection, segmentation and
            original views. Validation flags indicate whether a finding
            warrants additional review.
          </p>
          <p className="subtle">
            Location estimates only appear when navigation information
            accompanies the survey.
          </p>
        </Panel>
      </div>

      <div className="section-heading">
        <h2>Integration architecture</h2>
      </div>

      <div className="architecture">
        <div>
          <strong>Frontend</strong>
          <small>ABYSSEYE UI</small>
        </div>
        <ArrowRight size={15} />
        <div>
          <strong>FastAPI</strong>
          <small>Analysis jobs</small>
        </div>
        <ArrowRight size={15} />
        <div>
          <strong>Inference Service</strong>
          <small>Provider abstraction</small>
        </div>
        <ArrowRight size={15} />
        <div>
          <strong>Hugging Face / Jetson</strong>
          <small>Model execution</small>
        </div>
      </div>

      <div className="grid-2 docs-grid">
        <Panel title="Asynchronous API Contract" icon={<Server size={16} />}>
          <div className="endpoint">
            <code>POST /api/v1/analyses</code>
            <p>
              Submit an image, settings and optional navigation data. Returns{' '}
              <code>analysis_id</code>.
            </p>
          </div>
          <div className="endpoint">
            <code>GET /api/v1/analyses/{'{analysis_id}'}</code>
            <p>
              Poll for status, progress, current stage and completed results.
            </p>
          </div>
          <p className="subtle">
            The current demonstration uses a local mock service with this
            contract. A real FastAPI service can replace it without changing the
            workflow UI.
          </p>
        </Panel>

        <Panel title="JSON Output Structure" icon={<Code2 size={16} />}>
          <pre className="docs-code">{JSON_EXAMPLE}</pre>
        </Panel>
      </div>

      <div className="security-note">
        <LockKeyhole size={20} />
        <span>
          Inference credentials belong on the server. The browser must never
          receive a Hugging Face API token.
        </span>
      </div>
    </>
  );
}
