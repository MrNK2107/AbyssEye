export interface SpatialTelemetry {
  latitude: number | null;
  longitude: number | null;
  position_error_radius_m: number | null;
  geolocation_quality: string;
  altitude_m: number | null;
  slant_range_m: number;
  across_track_m: number;
  heading_deg: number | null;
}

export interface AcousticPhysicsEvidence {
  highlight_present: boolean;
  highlight_mean_intensity: number;
  highlight_peak_intensity: number;
  highlight_area_px: number;
  highlight_aspect_ratio: number;
  shadow_present: boolean;
  shadow_darkness: number;
  shadow_length_m: number;
  shadow_area_px: number;
  estimated_target_height_m: number;
  collinearity_score: number;
  grazing_angle_deg: number;
  physical_consistency_score: number;
}

export interface FilamentEvidence {
  filament_density: number;
  mesh_periodicity_index: number;
  boundary_tortuosity: number;
  is_net_like: boolean;
}

export interface SeabedContextEvidence {
  glcm_contrast_diff: number;
  glcm_homogeneity_diff: number;
  glcm_energy_diff: number;
  glcm_entropy_diff: number;
  gradient_var_diff: number;
  embedding_cosine_distance: number;
  seabed_roughness: number;
  isolation_score: number;
}

export interface TemporalTrackingEvidence {
  track_id: string;
  hits: number;
  total_window: number;
  persistence_ratio: number;
  status: string;
  position_residual_rms: number;
}

export interface ShapFeatureImpact {
  feature: string;
  value: number;
  shap_impact: number;
}

export interface CalibratedProbabilities {
  p_anthropogenic: number;
  p_natural: number;
  p_uncertain: number;
}

export interface FusionDecision {
  raw_logit: number;
  calibrated_probabilities: CalibratedProbabilities;
  triage_state: string;
  top_shap_features: ShapFeatureImpact[];
}

export interface HumanReview {
  reviewed_by: string | null;
  review_timestamp: string | null;
  decision: string | null;
  notes: string | null;
  target_subtype?: string;
  confidence_rating?: number;
}

export interface ContactDigitalTwin {
  contact_id: string;
  survey_id: string;
  frame_id: string;
  ping_index: number;
  bbox: [number, number, number, number];
  centroid: [number, number];
  channel: string;
  triage_state: 'HIGH_CONFIDENCE' | 'REVIEW' | 'NATURAL_SEABED' | string;
  target_type_hint: string;
  spatial_telemetry: SpatialTelemetry;
  evidence_graph: {
    discovery: {
      sources: string[];
      confidence: number;
      anomaly_score: number;
    };
    acoustic_physics: AcousticPhysicsEvidence;
    filament_netting: FilamentEvidence;
    seabed_context: SeabedContextEvidence;
    temporal_tracking: TemporalTrackingEvidence | null;
  };
  fusion_decision: FusionDecision;
  feature_vector: Record<string, number>;
  crop_image_base64?: string;
  beam_profile?: Array<{
    sample_idx: number;
    range_offset_m: number;
    intensity: number;
    region: string;
  }>;
  human_review: HumanReview;
}
