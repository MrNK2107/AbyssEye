'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

export interface Detection {
  id: string;
  class_name: string;
  confidence: number;
  raw_confidence: number;
  validated: boolean;
  bbox: [number, number, number, number]; // [x, y, width, height] in percentages (0-100)
  mask: number[][]; // [[x, y], [x, y], ...]
  location?: {
    latitude: number;
    longitude: number;
  } | null;
}

export interface SampleItem {
  id: string;
  title: string;
  category: string;
  description: string;
  image: string;
  quality: string;
  detections: Detection[];
}

export interface AnalysisResult {
  analysis_id: string;
  status: string;
  source_name: string;
  image_url: string;
  sample_id?: string;
  created_at: string;
  processing_seconds: number;
  model: string;
  threshold: number;
  context_validation: boolean;
  navigation_data: boolean;
  dimensions: {
    width: number;
    height: number;
  };
  detections: Detection[];
}

export interface AnalysisStats {
  analyses: number;
  images: number;
  detections: number;
}

interface AnalysisContextType {
  uploadUrl: string | null;
  createUploadUrl: (file: File) => string;
  clearUploadUrl: () => void;
  sample: SampleItem | null;
  setSample: (sample: SampleItem | null) => void;
  result: AnalysisResult | null;
  setResult: (result: AnalysisResult | null) => void;
  stats: AnalysisStats;
  recordAnalysis: (result: AnalysisResult) => void;
}

const defaultStats: AnalysisStats = {
  analyses: 0,
  images: 0,
  detections: 0,
};

const AnalysisContext = createContext<AnalysisContextType | null>(null);

export function AnalysisProvider({ children }: { children: React.ReactNode }) {
  const [sample, setSample] = useState<SampleItem | null>(null);
  const [uploadUrl, setUploadUrl] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [stats, setStats] = useState<AnalysisStats>(defaultStats);

  useEffect(() => {
    try {
      const stored = localStorage.getItem('abysseye-stats');
      if (stored) {
        const parsed = JSON.parse(stored);
        if (
          typeof parsed.analyses === 'number' &&
          typeof parsed.images === 'number' &&
          typeof parsed.detections === 'number'
        ) {
          setStats(parsed);
        }
      }
    } catch {
      // LocalStorage unavailable
    }
  }, []);

  function clearUploadUrl() {
    setUploadUrl((prev) => {
      if (prev && prev.startsWith('blob:')) {
        URL.revokeObjectURL(prev);
      }
      return null;
    });
  }

  function createUploadUrl(file: File) {
    const url = URL.createObjectURL(file);
    setUploadUrl((prev) => {
      if (prev && prev.startsWith('blob:')) {
        URL.revokeObjectURL(prev);
      }
      return url;
    });
    return url;
  }

  function recordAnalysis(newResult: AnalysisResult) {
    setResult(newResult);
    setStats((prev) => {
      const updated = {
        analyses: prev.analyses + 1,
        images: prev.images + 1,
        detections: prev.detections + newResult.detections.length,
      };
      try {
        localStorage.setItem('abysseye-stats', JSON.stringify(updated));
      } catch {
        // Ignored
      }
      return updated;
    });
  }

  return (
    <AnalysisContext.Provider
      value={{
        uploadUrl,
        createUploadUrl,
        clearUploadUrl,
        sample,
        setSample,
        result,
        setResult,
        stats,
        recordAnalysis,
      }}
    >
      {children}
    </AnalysisContext.Provider>
  );
}

export function useAnalysis() {
  const context = useContext(AnalysisContext);
  if (!context) {
    throw new Error('useAnalysis must be used within an AnalysisProvider');
  }
  return context;
}
