import { Detection, SampleItem } from '@/context/AnalysisContext';

export const SONAR_IMAGES = {
  ghost: '/assets/sonar-ghost-DRVGWC3r.jpg',
  pipeline: '/assets/sonar-pipeline-DF5qh4Sd.jpg',
  wreck: '/assets/sonar-wreck-Cuez3mbx.jpg',
  drum: '/assets/sonar-drum-CXLeJ3_Y.jpg',
};

export const makeDetection = (
  id: string,
  class_name: string,
  confidence: number,
  bbox: [number, number, number, number],
  validated: boolean = true
): Detection => ({
  id,
  class_name,
  confidence,
  raw_confidence: Math.max(0, Number((confidence - 0.07).toFixed(2))),
  validated,
  bbox,
  mask: [
    [bbox[0] + 2, bbox[1] + 3],
    [bbox[0] + bbox[2] - 3, bbox[1] + 2],
    [bbox[0] + bbox[2] - 2, bbox[1] + bbox[3] - 3],
    [bbox[0] + 3, bbox[1] + bbox[3] - 2],
  ],
});

export const SAMPLES: SampleItem[] = [
  {
    id: 'ghost-clear',
    title: 'Ghost Net — Clear',
    category: 'Ghost Net',
    description: 'Well-defined fishing net pattern with strong return.',
    image: SONAR_IMAGES.ghost,
    quality: 'High',
    detections: [makeDetection('DET-001', 'Ghost Net', 0.93, [13, 18, 32, 57])],
  },
  {
    id: 'ghost-low',
    title: 'Ghost Net — Low Contrast',
    category: 'Ghost Net',
    description: 'Partially buried net in a noisy background.',
    image: SONAR_IMAGES.ghost,
    quality: 'Moderate',
    detections: [makeDetection('DET-002', 'Ghost Net', 0.76, [16, 22, 31, 49], false)],
  },
  {
    id: 'gear-traps',
    title: 'Fishing Gear — Traps',
    category: 'Fishing Gear',
    description: 'Discarded trap and lines on the seabed.',
    image: SONAR_IMAGES.drum,
    quality: 'High',
    detections: [makeDetection('DET-003', 'Fishing Gear / Other', 0.82, [21, 60, 19, 22])],
  },
  {
    id: 'gear-rope',
    title: 'Fishing Gear — Rope',
    category: 'Fishing Gear',
    description: 'Thin rope-like structure across the survey.',
    image: SONAR_IMAGES.drum,
    quality: 'Moderate',
    detections: [makeDetection('DET-004', 'Fishing Gear / Other', 0.71, [16, 54, 24, 30], false)],
  },
  {
    id: 'pipe-strong',
    title: 'Pipeline — Strong Return',
    category: 'Pipeline / Cable',
    description: 'Exposed pipeline with a clear acoustic shadow.',
    image: SONAR_IMAGES.pipeline,
    quality: 'High',
    detections: [makeDetection('DET-005', 'Pipeline / Cable', 0.88, [5, 11, 89, 66])],
  },
  {
    id: 'pipe-buried',
    title: 'Pipeline — Partial Burial',
    category: 'Pipeline / Cable',
    description: 'Partially buried pipeline in irregular seabed.',
    image: SONAR_IMAGES.pipeline,
    quality: 'Moderate',
    detections: [makeDetection('DET-006', 'Pipeline / Cable', 0.79, [8, 23, 81, 55])],
  },
  {
    id: 'drum',
    title: 'Drum / Barrel',
    category: 'Drum / Barrel',
    description: 'Metallic barrel with a strong acoustic return.',
    image: SONAR_IMAGES.drum,
    quality: 'High',
    detections: [makeDetection('DET-007', 'Drum / Barrel', 0.84, [22, 20, 19, 29])],
  },
  {
    id: 'wreck',
    title: 'Shipwreck',
    category: 'Wreck',
    description: 'Wreck structure with complex geometry.',
    image: SONAR_IMAGES.wreck,
    quality: 'High',
    detections: [makeDetection('DET-008', 'Wreck', 0.81, [12, 17, 29, 44])],
  },
  {
    id: 'mixed',
    title: 'Mixed Debris',
    category: 'Mixed Debris',
    description: 'Multiple targets across a single survey strip.',
    image: SONAR_IMAGES.drum,
    quality: 'Moderate',
    detections: [
      makeDetection('DET-009', 'Drum / Barrel', 0.86, [22, 20, 19, 29]),
      makeDetection('DET-010', 'Fishing Gear / Other', 0.73, [17, 58, 25, 27], false),
    ],
  },
  {
    id: 'no-target',
    title: 'Natural Seabed',
    category: 'No Target',
    description: 'Seabed texture without confirmed targets.',
    image: SONAR_IMAGES.wreck,
    quality: 'High',
    detections: [],
  },
  {
    id: 'low-quality',
    title: 'High Noise',
    category: 'Low Quality',
    description: 'Low-quality sonar image with speckle artifacts.',
    image: SONAR_IMAGES.ghost,
    quality: 'Low',
    detections: [makeDetection('DET-011', 'Ghost Net', 0.57, [12, 19, 35, 55], false)],
  },
  {
    id: 'unknown',
    title: 'Unknown Object',
    category: 'Mixed Debris',
    description: 'Unclassified man-made object for review.',
    image: SONAR_IMAGES.wreck,
    quality: 'Moderate',
    detections: [makeDetection('DET-012', 'Fishing Gear / Other', 0.65, [76, 20, 17, 23], false)],
  },
];

export const CATEGORIES = [
  'All',
  'Ghost Net',
  'Fishing Gear',
  'Pipeline / Cable',
  'Drum / Barrel',
  'Wreck',
  'Mixed Debris',
  'No Target',
  'Low Quality',
];

export const TARGET_CLASSES = [
  'Ghost Net',
  'Pipeline / Cable',
  'Drum / Barrel',
  'Wreck',
  'Fishing Gear / Other',
];

export const PIPELINE_STAGES = [
  'Input Validation',
  'Sonar Preprocessing',
  'Image Tiling',
  'AI Detection & Segmentation',
  'Cross-Tile Fusion',
  'Context Validation',
  'Geolocation',
];

export const CLASS_COLORS: Record<string, string> = {
  'Ghost Net': 'target-red',
  'Pipeline / Cable': 'target-blue',
  'Drum / Barrel': 'target-green',
  Wreck: 'target-amber',
  'Fishing Gear / Other': 'target-violet',
};
