'use client';

import React, { useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { Search, ArrowRight } from 'lucide-react';
import { useAnalysis, SampleItem } from '@/context/AnalysisContext';
import { PageHeading, ClassTag } from '@/components/PageUi';
import { SAMPLES, CATEGORIES } from '@/lib/prototypeData';

export default function SamplesPage() {
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const router = useRouter();
  const { setSample, clearUploadUrl } = useAnalysis();

  const filteredSamples = useMemo(() => {
    return SAMPLES.filter((sample) => {
      const matchesCategory =
        selectedCategory === 'All' || sample.category === selectedCategory;
      const matchesQuery = `${sample.title} ${sample.description} ${sample.category}`
        .toLowerCase()
        .includes(searchQuery.toLowerCase());
      return matchesCategory && matchesQuery;
    });
  }, [selectedCategory, searchQuery]);

  function handleSelectSample(sample: SampleItem) {
    setSample(sample);
    clearUploadUrl();
    router.push('/analyze');
  }

  return (
    <>
      <PageHeading
        eyebrow="DEMONSTRATION DATASET"
        title="Sample Library"
        description="Explore side-scan sonar surveys and send a sample directly to analysis."
        action={
          <label className="search-wrap">
            <Search size={16} />
            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search samples..."
              aria-label="Search samples"
            />
          </label>
        }
      />

      <div className="filter-row" role="group" aria-label="Filter samples">
        {CATEGORIES.map((cat) => {
          const isActive = selectedCategory === cat;
          const count =
            cat === 'All'
              ? SAMPLES.length
              : SAMPLES.filter((s) => s.category === cat).length;

          return (
            <button
              key={cat}
              type="button"
              className={`inline-flex items-center justify-center gap-1.5 whitespace-nowrap text-xs font-medium cursor-pointer transition-colors h-8 rounded-md px-3 ${
                isActive
                  ? 'bg-primary text-primary-foreground shadow'
                  : 'border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground'
              }`}
              onClick={() => setSelectedCategory(cat)}
            >
              {cat} <span className="filter-count">{count}</span>
            </button>
          );
        })}
      </div>

      <div className="sample-grid">
        {filteredSamples.map((sample) => (
          <article className="sample-card" key={sample.id}>
            <div className="sample-image">
              <img
                src={sample.image}
                alt={`${sample.title} sonar scan`}
                loading="lazy"
                width={1280}
                height={720}
              />
              <span className="sample-badge">
                {sample.detections.length ? (
                  <ClassTag
                    name={
                      sample.detections[0]?.class_name ?? 'Fishing Gear / Other'
                    }
                  />
                ) : (
                  <span className="class-tag">{sample.category}</span>
                )}
              </span>
              <span className="scale-bar">50 m ━━━</span>
            </div>
            <div className="sample-body">
              <strong>{sample.title}</strong>
              <p>{sample.description}</p>
              <div className="sample-meta">
                1280 × 720 <span>·</span> {sample.quality} quality
              </div>
              <button
                type="button"
                className="w-full inline-flex items-center justify-center gap-2 whitespace-nowrap text-xs font-medium cursor-pointer transition-colors border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground h-8 rounded-md px-3"
                onClick={() => handleSelectSample(sample)}
              >
                Use This Sample <ArrowRight size={14} />
              </button>
            </div>
          </article>
        ))}
      </div>

      {!filteredSamples.length && (
        <div className="empty-state">No samples match your search.</div>
      )}
    </>
  );
}
