'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import {
  Download,
  Printer,
  ScanSearch,
  FileText,
  ArrowRight,
  Code2,
  FileCode2,
} from 'lucide-react';
import { useAnalysis } from '@/context/AnalysisContext';
import { PageHeading, Panel, ClassTag, StatCard } from '@/components/PageUi';
import { TARGET_CLASSES } from '@/lib/prototypeData';

export default function ReportsPage() {
  const { result } = useAnalysis();
  const [showJson, setShowJson] = useState(false);

  function exportCSV() {
    if (!result) return;
    const rows = [
      [
        'id',
        'class_name',
        'confidence',
        'raw_confidence',
        'validated',
        'bbox_x',
        'bbox_y',
        'bbox_width',
        'bbox_height',
        'latitude',
        'longitude',
      ],
      ...result.detections.map((d) => [
        d.id,
        d.class_name,
        d.confidence,
        d.raw_confidence,
        d.validated,
        ...d.bbox,
        d.location?.latitude ?? '',
        d.location?.longitude ?? '',
      ]),
    ];

    const csvContent = rows
      .map((row) =>
        row.map((val) => `"${String(val).replaceAll('"', '""')}"`).join(',')
      )
      .join('\r\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `abysseye-${result.analysis_id}.csv`;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  return (
    <>
      <PageHeading
        eyebrow="ANALYSIS / EXPORT"
        title="Reports"
        description="A structured overview of sonar analysis results and model output."
        action={
          result && (
            <div className="result-actions">
              <button
                type="button"
                className="inline-flex items-center justify-center gap-1.5 whitespace-nowrap text-xs font-medium cursor-pointer transition-colors border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground h-8 rounded-md px-3"
                onClick={exportCSV}
              >
                <Download size={14} /> Export CSV
              </button>
              <button
                type="button"
                className="inline-flex items-center justify-center gap-1.5 whitespace-nowrap text-xs font-medium cursor-pointer transition-colors bg-primary text-primary-foreground shadow hover:bg-primary/90 h-8 rounded-md px-3"
                onClick={() => window.print()}
              >
                <Printer size={14} /> Export PDF
              </button>
            </div>
          )
        }
      />

      {result ? (
        <div className="report-content">
          <div className="report-banner">
            <div>
              <span className="eyebrow">SONAR SURVEY REPORT</span>
              <h2>{result.source_name}</h2>
              <p>
                Analysis ID: {result.analysis_id} ·{' '}
                {new Date(result.created_at).toLocaleString()}
              </p>
            </div>
            <span className="complete-pill">● Analysis Completed</span>
          </div>

          <div className="grid-4">
            <StatCard
              icon={<ScanSearch size={20} />}
              label="Total Detections"
              value={result.detections.length}
            />
            <StatCard
              icon={<ScanSearch size={20} />}
              label="Validated Targets"
              value={result.detections.filter((d) => d.validated).length}
            />
            <StatCard
              icon={<ScanSearch size={20} />}
              label="Avg. Confidence"
              value={
                result.detections.length
                  ? `${Math.round(
                      (result.detections.reduce(
                        (acc, d) => acc + d.confidence,
                        0
                      ) /
                        result.detections.length) *
                        100
                    )}%`
                  : '—'
              }
            />
            <StatCard
              icon={<ScanSearch size={20} />}
              label="Processing Time"
              value={`${result.processing_seconds}s`}
            />
          </div>

          <div className="report-two">
            <Panel
              title="Sonar Input & Detections"
              icon={<ScanSearch size={16} />}
            >
              <div className="report-preview">
                <img
                  src={result.image_url}
                  alt="Analyzed sonar image"
                  width={1280}
                  height={720}
                />
                {result.detections.map((d) => (
                  <div
                    key={d.id}
                    className="report-box"
                    style={{
                      left: `${d.bbox[0]}%`,
                      top: `${d.bbox[1]}%`,
                      width: `${d.bbox[2]}%`,
                      height: `${d.bbox[3]}%`,
                    }}
                  />
                ))}
              </div>
              <p className="subtle">
                {result.source_name} · {result.dimensions.width} ×{' '}
                {result.dimensions.height} px
              </p>
            </Panel>

            <Panel title="Detection Distribution" icon={<ScanSearch size={16} />}>
              <div className="distribution">
                {TARGET_CLASSES.map((cls) => {
                  const count = result.detections.filter(
                    (d) => d.class_name === cls
                  ).length;
                  const pct = result.detections.length
                    ? (count / result.detections.length) * 100
                    : 0;

                  return (
                    <div key={cls}>
                      <span>{cls}</span>
                      <div className="progress-track">
                        <div
                          className="progress-fill"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                      <strong>{count}</strong>
                    </div>
                  );
                })}
              </div>

              <div className="divider" />

              {[
                ['Model', result.model],
                ['Threshold', result.threshold.toFixed(2)],
                [
                  'Validation',
                  result.context_validation ? 'Enabled' : 'Disabled',
                ],
                [
                  'Navigation',
                  result.navigation_data ? 'Provided' : 'Not provided',
                ],
              ].map(([k, v]) => (
                <div key={k} className="info-row">
                  <span>{k}</span>
                  <span>{v}</span>
                </div>
              ))}
            </Panel>
          </div>

          <Panel
            title={`Detected Targets (${result.detections.length})`}
            icon={<ScanSearch size={16} />}
          >
            <div className="report-table-wrap">
              <table className="report-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Class</th>
                    <th>Confidence</th>
                    <th>Validation</th>
                    <th>Location</th>
                  </tr>
                </thead>
                <tbody>
                  {result.detections.map((d) => (
                    <tr key={d.id}>
                      <td>{d.id}</td>
                      <td>
                        <ClassTag name={d.class_name} />
                      </td>
                      <td>{Math.round(d.confidence * 100)}%</td>
                      <td
                        className={
                          d.validated ? 'valid-text' : 'review-text'
                        }
                      >
                        {d.validated ? 'Validated' : 'Review'}
                      </td>
                      <td>
                        {d.location
                          ? `${d.location.latitude.toFixed(4)}, ${d.location.longitude.toFixed(4)}`
                          : 'Not available'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {!result.detections.length && (
                <p className="subtle">
                  No targets exceeded the selected threshold.
                </p>
              )}
            </div>
          </Panel>

          <Panel title="Model Output (JSON)" icon={<FileCode2 size={16} />}>
            <p className="subtle">
              Structured analysis response: detections include class labels,
              confidence, normalized bounding boxes, segmentation polygons,
              validation status and optional location.
            </p>
            <button
              type="button"
              className="inline-flex items-center justify-center gap-1.5 whitespace-nowrap text-xs font-medium cursor-pointer transition-colors border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground h-8 rounded-md px-3"
              onClick={() => setShowJson((prev) => !prev)}
            >
              <Code2 size={14} /> {showJson ? 'Hide' : 'Show'} JSON output
            </button>
            {showJson && (
              <pre className="json-block">
                {JSON.stringify(result, null, 2)}
              </pre>
            )}
          </Panel>
        </div>
      ) : (
        <div className="report-empty">
          <FileText size={40} />
          <h2>No report available yet</h2>
          <p>
            Run an analysis to view target findings, inspect structured output
            and export your report.
          </p>
          <Link
            href="/analyze"
            className="inline-flex items-center justify-center gap-2 whitespace-nowrap text-sm font-medium cursor-pointer transition-colors bg-primary text-primary-foreground shadow hover:bg-primary/90 h-9 rounded-md px-4"
          >
            Start Analysis <ArrowRight size={14} />
          </Link>
        </div>
      )}
    </>
  );
}
