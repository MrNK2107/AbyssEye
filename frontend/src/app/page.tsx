'use client';

import React from 'react';
import Link from 'next/link';
import {
  ArrowRight,
  Images,
  Layers,
  ScanSearch,
  ShieldCheck,
  MapPin,
  Radar,
  CircleDot,
  Waves,
} from 'lucide-react';
import { useAnalysis } from '@/context/AnalysisContext';
import { StatCard } from '@/components/PageUi';
import { SONAR_IMAGES } from '@/lib/prototypeData';

const PROCESS_STEPS = [
  {
    n: '01',
    t: 'Upload sonar imagery',
    d: 'Use your own side-scan survey image or choose a sample.',
    img: SONAR_IMAGES.ghost,
    icon: Images,
  },
  {
    n: '02',
    t: 'Detect & segment',
    d: 'Locate targets with boxes, masks, labels and confidence.',
    img: SONAR_IMAGES.pipeline,
    icon: ScanSearch,
  },
  {
    n: '03',
    t: 'Validate context',
    d: 'Review acoustic shadows and surrounding seabed context.',
    img: SONAR_IMAGES.drum,
    icon: ShieldCheck,
  },
  {
    n: '04',
    t: 'Locate targets',
    d: 'Add GPS/INS data for optional location context.',
    img: SONAR_IMAGES.wreck,
    icon: MapPin,
  },
];

export default function HomePage() {
  const { stats } = useAnalysis();

  return (
    <>
      <div className="home-hero">
        <img
          src={SONAR_IMAGES.pipeline}
          alt="Side-scan sonar survey showing a submerged pipeline"
          width={1280}
          height={720}
        />
        <div className="home-hero-copy">
          <div className="eyebrow">EXPLORE · DETECT · UNDERSTAND</div>
          <h1>
            See the Unseen
            <br />
            Beneath <span>the Surface</span>
          </h1>
          <p>
            ABYSSEYE uses AI to detect, validate and locate underwater targets
            in side-scan sonar imagery—turning complex surveys into actionable
            insight.
          </p>
          <div className="hero-actions">
            <Link
              href="/analyze"
              className="inline-flex items-center justify-center gap-2 whitespace-nowrap text-sm font-medium cursor-pointer transition-colors bg-primary text-primary-foreground shadow hover:bg-primary/90 h-10 rounded-md px-8"
            >
              <ArrowRight size={16} /> Start Analysis
            </Link>
            <Link
              href="/samples"
              className="inline-flex items-center justify-center gap-2 whitespace-nowrap text-sm font-medium cursor-pointer transition-colors border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground h-10 rounded-md px-8"
            >
              <Images size={16} /> Explore Sample Library
            </Link>
          </div>
        </div>
        <span className="hero-readout">SIDE-SCAN SONAR / SURVEY 001</span>
      </div>

      <div className="grid-4 home-stats">
        <StatCard
          label="Analyses Processed"
          value={stats.analyses}
          icon={<Layers size={20} />}
          note="This browser"
        />
        <StatCard
          label="Images Analyzed"
          value={stats.images}
          icon={<Images size={20} />}
          note="This browser"
        />
        <StatCard
          label="Detections Found"
          value={stats.detections}
          icon={<ScanSearch size={20} />}
          note="Across analyses"
        />
        <StatCard
          label="Validated Targets"
          value="Context-aware"
          icon={<ShieldCheck size={20} />}
          note="Review in Analyze"
        />
      </div>

      <div className="section-heading">
        <h2>How it works</h2>
        <Link href="/documentation">Explore documentation →</Link>
      </div>

      <div className="grid-4 process-grid">
        {PROCESS_STEPS.map((step) => {
          const StepIcon = step.icon;
          return (
            <div key={step.n} className="process-item">
              <div className="process-label">
                <span>{step.n}</span>
                <StepIcon size={16} />
                {step.t}
              </div>
              <img
                src={step.img}
                alt="Side-scan sonar example"
                loading="lazy"
                width={1280}
                height={720}
              />
              <p>{step.d}</p>
            </div>
          );
        })}
      </div>

      <div className="home-bottom">
        <span>
          <Radar size={18} /> GHOST NETS
        </span>
        <span>
          <CircleDot size={18} /> PIPELINES
        </span>
        <span>
          <Layers size={18} /> DEBRIS
        </span>
        <span>
          <Waves size={18} /> SIDE-SCAN SONAR
        </span>
      </div>
    </>
  );
}
