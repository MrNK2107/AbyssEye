'use client';

import React from 'react';
import Link from 'next/link';
import { ArrowRight, Eye, Layers, ScanSearch, Waves } from 'lucide-react';
import { PageHeading, Panel } from '@/components/PageUi';
import { SONAR_IMAGES } from '@/lib/prototypeData';

export default function AboutPage() {
  return (
    <>
      <PageHeading
        eyebrow="ABOUT THE PLATFORM"
        title="About ABYSSEYE"
        description="Clarity for the underwater world."
      />

      <div className="about-lead">
        <div>
          <span className="eyebrow">OUR PURPOSE</span>
          <h2>Making underwater survey data easier to understand.</h2>
          <p>
            Side-scan sonar reveals what lies beneath the surface, but
            interpreting its imagery can be slow, demanding and subjective.
            ABYSSEYE helps survey teams surface likely targets quickly while
            keeping analysts in control of the final decision.
          </p>
          <Link
            href="/analyze"
            className="inline-flex items-center justify-center gap-2 whitespace-nowrap text-sm font-medium cursor-pointer transition-colors bg-primary text-primary-foreground shadow hover:bg-primary/90 h-9 rounded-md px-4"
          >
            Explore Analyze <ArrowRight size={14} />
          </Link>
        </div>
        <img
          src={SONAR_IMAGES.ghost}
          alt="Side-scan sonar imagery showing a ghost net"
          width={1280}
          height={720}
        />
      </div>

      <div className="section-heading">
        <h2>The challenge and our approach</h2>
      </div>

      <div className="grid-3">
        <Panel title="The Problem" icon={<Waves size={16} />}>
          <p className="subtle">
            Underwater surveys produce large volumes of noisy, low-contrast
            imagery. Ghost nets, infrastructure and debris can be difficult to
            distinguish from natural seabed features.
          </p>
        </Panel>

        <Panel title="The Approach" icon={<ScanSearch size={16} />}>
          <p className="subtle">
            AI-assisted detection and instance segmentation identify candidate
            objects, while context validation helps flag uncertain results for
            human review.
          </p>
        </Panel>

        <Panel title="The Outcome" icon={<Eye size={16} />}>
          <p className="subtle">
            A clear analysis workspace brings imagery, detections, confidence,
            validation and optional geolocation into one reviewable result.
          </p>
        </Panel>
      </div>

      <div className="about-principles">
        <Layers size={24} />
        <div>
          <h3>Built for human-in-the-loop analysis</h3>
          <p>
            ABYSSEYE supports analysts; it does not replace expert
            interpretation. Every detection remains inspectable, and prototype
            results should be independently verified before operational use.
          </p>
        </div>
      </div>
    </>
  );
}
