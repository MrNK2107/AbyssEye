# ABYSSEYE — System Architecture & Dataflow Specification

**Document Version:** v3.0  
**Target:** SIH 2026 Problem Statement 26057  
**System Name:** ABYSSEYE (Autonomous Bathymetric & Side-Scan Sonar Evidence Engine)

---

## 1. High-Level Architecture Overview

ABYSSEYE is engineered as a decoupled, multi-tiered asynchronous system designed to process complex high-resolution Side-Scan Sonar (SSS) data streams and provide calibrated, physics-verified contact intelligence.

```
+─────────────────────────────────────────────────────────────────────────+
|                        TIER 1: INGESTION & DATAFLOW                     |
|  Raw Sonar (XTF, JSF, GeoTIFF, Waterfall) → Ingestion Parser → QC Engine |
+─────────────────────────────────────────────────────────────────────────+
                                     │
                                     ▼
+─────────────────────────────────────────────────────────────────────────+
|                       TIER 2: ML INFERENCE PIPELINE                     |
|                                                                         |
|  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐   |
|  │  Classical CV    │    │ PatchCore Anomaly│    │  YOLOv8/RT-DETR  │   |
|  │ (Adaptive/Otsu)  │    │  (WideResNet50)  │    │  (Supervised)    │   |
|  └────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘   |
|           └───────────────────────┼───────────────────────┘             |
|                                   ▼                                     |
|                       Candidate Proposal Fusion                         |
|                                   │                                     |
|                                   ▼                                     |
|                     Acoustic Physics Verification                       |
|                   (Highlight, Shadow, Collinearity)                     |
|                                   │                                     |
|                                   ▼                                     |
|                       Multi-Ping Kalman Tracker                         |
|                     (Hungarian Data Association)                        |
|                                   │                                     |
|                                   ▼                                     |
|                         Seabed Context Module                           |
|                      (GLCM Texture + Embedding)                         |
|                                   │                                     |
|                                   ▼                                     |
|                        LightGBM Evidence Fusion                         |
|                     + Platt/Isotonic Calibration                        |
+─────────────────────────────────────────────────────────────────────────+
                                     │
                                     ▼
+─────────────────────────────────────────────────────────────────────────+
|                     TIER 3: BACKEND ENGINE (FastAPI)                    |
|   • Asynchronous Job Queue (Celery / BackgroundTasks)                   |
|   • PostgreSQL / PostGIS Spatial Database & JSONB Evidence Store        |
|   • Georeferencing & Ray-Tracing Navigation Transformer                 |
|   • REST API & WebSocket Live Alert Broadcaster                        |
+─────────────────────────────────────────────────────────────────────────+
                                     │
                                     ▼
+─────────────────────────────────────────────────────────────────────────+
|               TIER 4: GIS MISSION INTERFACE (Next.js / Leaflet)          |
|   • Interactive Bathymetric Trackline & Swath Coverage Viewer           |
|   • Real-time Contact Triage Queue (High Confidence / Review / Natural) |
|   • Contact Digital Twin & Physics Evidence Card (SHAP & Waterfall)     |
|   • 1-Click Active Learning Annotation Modal                            |
+─────────────────────────────────────────────────────────────────────────+
```

---

## 2. The Contact Digital Twin & Evidence Graph

At the heart of ABYSSEYE is the **Contact Digital Twin (CDT)**. A contact is not just a bounding box on an image; it is an evolving spatial-temporal entity with a persistent Evidence Graph that records every observation, physical measurement, and model decision across sequential sonar pings.

### 2.1 Contact Digital Twin Schema (JSON)

```json
{
  "contact_id": "CONT-2026-0927-00142",
  "survey_id": "SRV-BALTIC-NORTH-04",
  "created_at": "2026-09-27T12:45:00.120Z",
  "status": "REVIEW",
  "triage_category": "POSSIBLE_ANTHROPOGENIC",
  
  "spatial_telemetry": {
    "latitude": 54.821945,
    "longitude": 18.734201,
    "position_error_radius_m": 2.4,
    "geolocation_quality": "HIGH",
    "altitude_m": 12.5,
    "slant_range_m": 42.8,
    "across_track_m": 40.9,
    "heading_deg": 184.2,
    "channel": "STARBOARD"
  },

  "evidence_graph": {
    "discovery": {
      "sources": ["classical_cv", "patchcore_anomaly"],
      "classical_confidence": 0.88,
      "patchcore_anomaly_score": 0.912,
      "detector_class": null,
      "detector_confidence": 0.0
    },
    
    "acoustic_physics": {
      "highlight_present": true,
      "highlight_peak_intensity": 242,
      "highlight_mean_intensity": 218.4,
      "highlight_area_px": 340,
      "shadow_present": true,
      "shadow_mean_darkness": 14.2,
      "shadow_length_m": 6.8,
      "estimated_target_height_m": 1.73,
      "collinearity_score": 0.94,
      "grazing_angle_deg": 16.9
    },

    "temporal_tracking": {
      "track_id": "TRK-0089",
      "pings_observed": 7,
      "pings_total_window": 8,
      "persistence_ratio": 0.875,
      "kalman_position_residual": 0.32,
      "velocity_consistency": 0.96
    },

    "seabed_context": {
      "surrounding_seabed_type": "SAND_RIPPLES",
      "glcm_contrast_diff": 48.2,
      "glcm_homogeneity_diff": 0.38,
      "embedding_cosine_distance": 0.642,
      "isolation_metric": 0.89
    }
  },

  "fusion_decision": {
    "model_version": "lightgbm-v3.0.4",
    "calibrator": "isotonic_regression_v3",
    "raw_logit": 2.14,
    "calibrated_probabilities": {
      "p_anthropogenic": 0.812,
      "p_natural": 0.131,
      "p_uncertain": 0.057
    },
    "top_shap_features": [
      {"feature": "shadow_length_m", "shap_value": 0.42},
      {"feature": "collinearity_score", "shap_value": 0.38},
      {"feature": "persistence_ratio", "shap_value": 0.31},
      {"feature": "embedding_cosine_distance", "shap_value": 0.24},
      {"feature": "glcm_contrast_diff", "shap_value": 0.18}
    ]
  },

  "human_review": {
    "reviewed_by": null,
    "review_timestamp": null,
    "decision": null,
    "notes": null
  }
}
```

---

## 3. Detailed Component Breakdown

### 3.1 Ingestion & Quality Control Engine
- **Supported Formats:**
  - `XTF` (eXtended Triton Format): Multi-channel sonar packets parsed via custom binary unpacker.
  - `JSF` (EdgeTech Sonar Format): High-frequency and low-frequency dual acoustic records.
  - `GeoTIFF`: Georeferenced bathymetric and backscatter rasters.
  - `Waterfall PNG/TIFF`: Raw scanline strips with accompanying sidecar `.json` navigation logs.
- **Quality Control Metrics:**
  - **SNR Estimation:** Ratio of backscatter signal power to nadir water-column noise.
  - **Clipping Detection:** Flags pings with $>5\%$ pixel saturation ($I \ge 254$).
  - **Blind-Zone / Altitude Loss:** Detects loss of bottom-lock tracking when altitude drops below $1.5\text{m}$.

### 3.2 Multi-Candidate Discovery Pipeline
- **Classical Proposal Engine:** 
  - Adaptive sliding-window background normalization $\mu_{\text{local}}, \sigma_{\text{local}}$.
  - Multi-scale Otsu thresholding + Morphological Close-Open filters.
  - Connected component extraction with geometric aspect-ratio filtering.
- **PatchCore Feature-Memory Anomaly Engine:**
  - Backbone: WideResNet50 / DINOv2 feature extractor.
  - Mid-level feature maps extracted (Layer 2 & 3), average-pooled, and indexed via Johnson-Lindenstrauss random projection & greedy coreset subsampling.
  - Generates dense spatial anomaly heatmap $A(x, y) \in [0, 1]$.
- **Supervised Known-Object Detector:**
  - YOLOv8x / RT-DETR model trained specifically on labeled benchmarks (SubPipe, SWDD, AI4Shipwrecks).
  - Emits candidate bounding boxes for `pipeline`, `wreck`, `mine`, and `wall`.

### 3.3 Acoustic Physics Verification Module
- **Highlight Segmenter:** Extracts bright acoustic returns adjacent to candidate centroids.
- **Beam Ray Tracer & Shadow Segmenter:** 
  - Traces outward along the sonar transmission vector away from the nadir line.
  - Applies local dark thresholding ($I < \mu_{\text{seabed}} - 1.5\sigma_{\text{seabed}}$).
- **Physical Feasibility Checker:**
  - Verifies that shadow falls **away** from the transducer.
  - Calculates collinearity vector angle $\theta_{\text{collinear}} = \arccos(\hat{v}_{\text{beam}} \cdot \hat{v}_{\text{highlight-to-shadow}})$. A valid contact must satisfy $\theta_{\text{collinear}} \le 15^\circ$.
  - Computes estimated physical height $h_t = \frac{H_a \cdot L_s}{R_s + L_s}$.

### 3.4 Multi-Ping Kalman Tracker
- **State Vector:** $\mathbf{x}_k = [x, y, v_x, v_y, w, h]^T$ in ground coordinate space.
- **Measurement Vector:** $\mathbf{z}_k = [x_m, y_m, w_m, h_m]^T$.
- **Data Association:** Hungarian (Munkres) assignment with gating based on Mahalanobis distance and visual embedding cosine similarity.
- **Track Lifecycle:**
  - `TENTATIVE`: Single observation.
  - `CONFIRMED`: Observed in $\ge 3$ out of 5 consecutive pings.
  - `LOST / TERMINATED`: Unobserved for $\ge 3$ consecutive pings.

### 3.5 LightGBM Calibrated Evidence Fusion
- **Tabular 32-Feature Vector:** Consolidated representation combining discovery confidence, physical dimensions, collinearity, track persistence, and GLCM seabed contrast.
- **LightGBM Binary/Multiclass Classifier:** Highly tuned gradient boosting trees with `max_depth=5`, `num_leaves=31`, `learning_rate=0.03`.
- **Probability Calibrator:** Isotonic regression fit on held-out validation folds to produce reliable $P(\text{Anthropogenic})$.
- **SHAP Engine:** TreeSHAP calculates exact per-contact feature attributions in $<2\text{ms}$.

---

## 4. Backend & Database Architecture

### 4.1 Tech Stack
- **Framework:** FastAPI (Python 3.11) with Uvicorn ASGI server.
- **Async Tasks:** Celery / Redis or FastAPI BackgroundTasks for batch sonar processing.
- **Database:** PostgreSQL 16 with **PostGIS** extension for geospatial geometries (tracklines, swaths, points) and **JSONB** indexing for the Evidence Graph.
- **ORM:** SQLAlchemy 2.0 with asyncpg driver and GeoAlchemy2.

### 4.2 Entity-Relationship Schema

```
┌──────────────────┐       1:N       ┌──────────────────┐
│     Surveys      ├─────────────────┤    SonarFrames   │
│  - survey_id     │                 │  - frame_id      │
│  - vessel_name   │                 │  - ping_number   │
│  - track_geom    │                 │  - altitude      │
│  - start_time    │                 │  - heading       │
└────────┬─────────┘                 │  - raw_path      │
         │                           └────────┬─────────┘
         │ 1:N                                │ 1:N
         │                                    │
┌────────┴─────────┐                 ┌────────┴─────────┐
│     Tracks       │       1:N       │     Contacts     │
│  - track_id      ├─────────────────┤  - contact_id    │
│  - pings_count   │                 │  - location_geom │
│  - persistence   │                 │  - evidence_json │
│  - avg_velocity  │                 │  - p_anthropo    │
└──────────────────┘                 │  - status (REV)  │
                                     └────────┬─────────┘
                                              │ 1:N
                                     ┌────────┴─────────┐
                                     │     Reviews      │
                                     │  - review_id     │
                                     │  - reviewer_name │
                                     │  - label_choice  │
                                     │  - notes         │
                                     └──────────────────┘
```

---

## 5. Security, Reliability & Failure Modes

| Failure Scenario | Mitigation Strategy | System Behavior |
|---|---|---|
| **Missing Navigation / GPS** | Fall back to pixel coordinate frame $(u, v)$ and relative across-track range. | Sets `geolocation_quality: UNAVAILABLE`; does not invent false coordinates. |
| **Acoustic Shadow Occluded / Absent** | Set `shadow_present: false`, `shadow_length_m: 0`. | Fusion model learns weights for shadow-less contacts; lowers physical confidence score without immediate rejection. |
| **Severe Bottom-Lock Failure** | Flag ping as `DEGRADED_QUALITY` during QC phase. | Down-weights height estimation features; displays alert banner on UI Evidence Card. |
| **PatchCore Out-of-Distribution Seabed** | High anomaly score triggered by natural coral/rocky reef. | Highlight-shadow physics and seabed GLCM texture difference features suppress false positive in LightGBM fusion. |
