# ABYSSEYE — SIH 2026 Problem Statement 26057
## Detailed Product Requirements Document (PRD) — Enhanced Technical Baseline v3.0

**Project:** ABYSSEYE  
**SIH Problem Statement:** 26057  
**Problem:** AI-Powered Automated Underwater Marine Debris and Anomaly Detection System using Side-Scan Sonar Imagery  
**Status:** Enhanced Implementation Baseline — v3.0  
**Repository Architecture:** Multi-module (ML Pipeline, FastAPI Backend, Next.js / Leaflet GIS Frontend)

---

## 1. Executive Summary

ABYSSEYE is an AI-assisted Side-Scan Sonar (SSS) analysis system for detecting anthropogenic underwater debris and anomalies against complex natural seabed backgrounds.

The foundational design shift from a conventional YOLO-only or segmentation-only architecture is that ABYSSEYE **does not depend on large supervised ghost-net segmentation datasets**. Public real SSS imagery for ghost nets and discarded fishing gear is extremely sparse, whereas real SSS data for subsea pipelines, shipwrecks, naval mines, revetment walls, and natural seabed morphology is well-documented and accessible.

Therefore, ghost nets and novel underwater debris are treated fundamentally as an **open-set anomaly and contact discovery problem**.

The frozen system workflow is:

```
Open-set Contact Discovery 
  → Acoustic Physics Verification 
    → Multi-Ping Tracking (Kalman / Hungarian) 
      → Seabed-Context Analysis 
        → Physics-Aware Evidence Representation 
          → Calibrated LightGBM Evidence Fusion 
            → Geolocation & GIS Evidence Cards
```

The system does not classify a sonar patch in isolation. It builds an auditable, multi-modal evidence chain evaluating:
1. **Acoustic anomaly score** (PatchCore memory bank trained on natural seabed),
2. **Acoustic physics behavior** (co-located highlight and acoustic shadow geometry),
3. **Temporal persistence** (track continuity across sequential pings),
4. **Contextual contrast** (target vs. immediate surrounding ring vs. global seabed background),
5. **Known-object detector predictions** (RT-DETR / YOLOv8 evidence where trained labels exist),
6. **Geometric & spatial constraints** (slant range, altitude, grazing angle, aspect ratio).

A lightweight **LightGBM contact-level fusion model** synthesizes heterogeneous discovery, acoustic, temporal, contextual, and spatial features into a calibrated probability distribution:
$$P(\text{Anthropogenic}), \quad P(\text{Natural}), \quad P(\text{Uncertain})$$

### Core Differentiator
> **ABYSSEYE does not classify a sonar pixel in isolation. It evaluates whether a contact behaves like a physical, rigid/semi-rigid object across acoustic, temporal, contextual, and spatial evidence, then exposes the exact evidence chain that produced the decision.**

---

## 2. Problem Definition & Operational Reality

Given raw or processed SSS imagery (waterfall strips, GeoTIFFs, XTF/JSF logs), the system must:
1. **Discover suspicious contacts** with high recall without relying on pre-existing class templates.
2. **Detect known anthropogenic objects** where genuine ground truth labels exist (pipelines, wrecks, mines).
3. **Surface unknown / open-set anomalies** (e.g., ghost fishing nets, abandoned gear, containers).
4. **Suppress natural seabed false positives** caused by sand ripples, rocky outcrops, boulder fields, and biological scattering.
5. **Enforce acoustic physics constraints** by analyzing highlight brightness, shadow darkness, shadow length, and grazing angle geometry.
6. **Exploit multi-ping persistence** by tracking contacts across adjacent sonar pings via state estimation.
7. **Provide explainable contact-level decisions** via human-readable Evidence Cards and SHAP feature attributions.
8. **Geolocate detections** with rigorous error bounds when vessel navigation and sonar geometry metadata exist.
9. **Empower human-in-the-loop review and active learning** to continuously refine fusion performance.

### Core Principle
> **An unusual sonar appearance is evidence of interest, not proof of debris.**

---

## 3. Goals & Non-Goals

### Primary Goals
- **High Candidate Recall:** >95% recall at the candidate discovery phase (Classical CV + PatchCore + Object Detector).
- **Physical Verification:** Quantify highlight-shadow co-occurrence, directionality, and length-to-height acoustics.
- **Temporal Verification:** Kalman filter + Hungarian algorithm association to eliminate transient speckle noise and ping dropouts.
- **Learned Evidence Fusion:** Replace arbitrary heuristic formulas ($0.3 \times \text{detector} + 0.2 \times \text{shadow}$) with a trained, interpretable LightGBM tabular fusion model.
- **Calibrated Uncertainty:** Apply Platt Scaling / Isotonic Regression to ensure output confidence reflects real empirical risk.
- **Operational GIS & Evidence Card UI:** Real-time interactive mission dashboard featuring Leaflet map tracks, side-by-side waterfall crops, acoustic profile plots, and 1-click review triage.

### Explicit Non-Goals
ABYSSEYE will **not**:
- Claim synthetic ghost-net imagery represents genuine real-world ground truth.
- Use optical marine-debris datasets as side-scan sonar ground truth.
- Require pixel-level supervised ghost-net segmentation masks.
- Fabricate navigation coordinates or physical dimensions when sonar metadata is missing.
- Treat PatchCore anomaly detection as a final deterministic class label.
- Treat every sonar tile as an independent physical observation (ignoring ping correlation).

---

## 4. User Personas

| Persona | Primary Needs | Key Interface |
|---|---|---|
| **Marine Survey Operator** | Rapid review of raw survey logs, high-confidence contact triage, GPS export | GIS Mission Map, Evidence Card, GeoJSON export |
| **AUV / ROV Navigation Team** | Low-latency contact alerts, target coordinates with confidence ellipses | REST / WebSocket API, Autonomous Alert Stream |
| **Marine Ecologist & Cleanup Crew** | Spatial clustering of ghost nets vs natural reefs, debris density heatmaps | Survey Summary Reports, Anomaly GIS Layers |
| **ML & Sonar Researcher** | Provenance tracking, raw feature vectors, SHAP attribution, active learning review | Benchmark Tool, Model Retraining CLI, Ablation Dashboard |

---

## 5. End-to-End System Workflow

```
+-------------------------------------------------------------------------+
|                              SONAR DATA                                 |
|            (XTF, JSF, GeoTIFF, Waterfall PNG/JPEG, Slant-Range)         |
+-------------------------------------------------------------------------+
                                     │
                                     ▼
+-------------------------------------------------------------------------+
|                       INGESTION & QUALITY CONTROL                       |
|   • File parsing (XTF / GeoTIFF / Image)   • Metadata sanity validation |
|   • Saturation & blind-zone detection      • Signal-to-noise ratio (SNR)|
+-------------------------------------------------------------------------+
                                     │
                                     ▼
+-------------------------------------------------------------------------+
|                             PREPROCESSING                               |
|   • Percentile & log intensity compression • Local TV/Lee speckle filter|
|   • Slant-range ground correction          • Port/Starboard channel sep |
+-------------------------------------------------------------------------+
                                     │
            ┌────────────────────────┼────────────────────────┐
            ▼                        ▼                        ▼
┌───────────────────────┐┌───────────────────────┐┌───────────────────────┐
│ CLASSICAL PROPOSALS   ││ PATCHCORE ANOMALY     ││ KNOWN-OBJECT DETECTOR │
│ • Local background est││ • WideResNet/DINO feat││ • RT-DETR / YOLOv8    │
│ • Adaptive threshold  ││ • Coreset memory bank ││ • Pipeline, Wreck,    │
│ • MSER / Blob filter  ││ • Pixel anomaly map   ││   Mine, Wall classes  │
└───────────────────────┘└───────────────────────┘└───────────────────────┘
            │                        │                        │
            └────────────────────────┼────────────────────────┘
                                     ▼
+-------------------------------------------------------------------------+
|                  CANDIDATE CONTACT REGION PROPOSALS                     |
|           • Multi-source non-maximum suppression / cluster merge        |
+-------------------------------------------------------------------------+
                                     │
                                     ▼
+-------------------------------------------------------------------------+
|                     ACOUSTIC PHYSICS VERIFICATION                       |
|   • Highlight extraction: intensity, centroid, area, aspect ratio       |
|   • Shadow extraction: dark pool segmentation along grazing beam vector |
|   • Geometry verification: distance, collinearity, height estimation    |
+-------------------------------------------------------------------------+
                                     │
                                     ▼
+-------------------------------------------------------------------------+
|                      MULTI-PING TRACKING (TEMPORAL)                     |
|   • Kalman Filter 2D state estimation (along-track / across-track)      |
|   • Hungarian assignment with spatial & appearance gating               |
|   • Track features: length, observation ratio, velocity consistency     |
+-------------------------------------------------------------------------+
                                     │
                                     ▼
+-------------------------------------------------------------------------+
|                         SEABED CONTEXT ANALYSIS                         |
|   • Multi-scale crops: [Target] vs. [Local Ring] vs. [Global Seabed]    |
|   • Texture metrics: GLCM contrast/homogeneity, gradient variance       |
|   • Learned seabed embedding distance (ResNet feature cosine distance)  |
+-------------------------------------------------------------------------+
                                     │
                                     ▼
+-------------------------------------------------------------------------+
|                         LIGHTGBM EVIDENCE FUSION                        |
|   • Synthesize 32 heterogeneous acoustic, discovery, temporal, context, │
|     and spatial features                                                |
|   • Compute raw logit score for Anthropogenic vs Natural vs Uncertain   |
+-------------------------------------------------------------------------+
                                     │
                                     ▼
+-------------------------------------------------------------------------+
|                         PROBABILITY CALIBRATION                         |
|   • Isotonic Regression / Platt Scaling on out-of-fold validation set   |
|   • Output: Calibrated P(Anthropogenic), P(Natural), P(Uncertain)       |
+-------------------------------------------------------------------------+
                                     │
                   ┌─────────────────┴─────────────────┐
                   ▼                                   ▼
+------------------------------------+ +----------------------------------+
|          GIS MISSION MAP           | |          EVIDENCE CARD           |
| • Georeferenced target markers     | | • Multi-channel sonar crops      |
| • Survey tracklines & swaths       | | • Highlight/shadow profile plot  |
| • Confidence heatmaps & exports    | | • SHAP explainability breakdown  |
+------------------------------------+ +----------------------------------+
                   │                                   │
                   └─────────────────┬─────────────────┘
                                     ▼
+-------------------------------------------------------------------------+
|                     OPERATOR TRIAGE & ACTIVE LEARNING                   |
|   • High Confidence (>0.80) | Review (0.40–0.80) | Natural (<0.40)      |
|   • 1-Click human annotation feedback loop into training registry       |
+-------------------------------------------------------------------------+
```

---

## 6. Functional Requirements Matrix

| ID | Module | Description | Acceptance Criteria |
|---|---|---|---|
| **FR-01** | Ingestion | Parse XTF, JSF, GeoTIFF, PNG/JPG waterfall files | Extracts metadata (frequency, range, coordinates, altitude, heading) or flags missing fields explicitly. |
| **FR-02** | Quality Control | Automatic sensor check for clipping, noise, blind zones | Generates QC status flag (`EXCELLENT`, `DEGRADED`, `CORRUPTED`) with SNR and saturation ratio. |
| **FR-03** | Preprocessing | Slant-range correction, percentile normalization, filtering | Preserves high-frequency acoustic shadow edges while attenuating background speckle. |
| **FR-04** | Classical Discovery | Adaptive local contrast, Otsu thresholding, connected components | Discovers 95%+ high-contrast target candidates in <50ms per frame. |
| **FR-05** | PatchCore Anomaly | Self-supervised memory bank anomaly discovery | Produces normalized anomaly heatmap and peak anomaly score per proposal. |
| **FR-06** | Known Detector | YOLOv8 / RT-DETR trained on labeled SSS benchmarks | Outputs bounding boxes, class names (`pipeline`, `wreck`, `mine`, etc.), and detector confidence. |
| **FR-07** | Highlight Physics | Peak intensity, area, orientation, centroid | Extracts bright acoustic reflection metrics relative to local background. |
| **FR-08** | Shadow Physics | Beam-aligned dark shadow segmentation | Identifies acoustic shadow region cast behind object relative to nadir/sonar path. |
| **FR-09** | Geometry Checks | Collinearity, grazing angle consistency, height estimation | Validates physical possibility: shadow must fall away from the sonar transducer. |
| **FR-10** | Multi-Ping Tracking | Kalman Filter + Hungarian data association | Associates candidates across $\ge 2$ consecutive pings within distance/appearance gates. |
| **FR-11** | Track Metrics | Calculate track length, persistence ratio, spatial residual | Distinguishes static physical targets from transient acoustic artifacts. |
| **FR-12** | Context Windows | Extract concentric nested crops: target, ring, scene | Extracts target $W \times H$, ring $2W \times 2H$, and background $4W \times 4H$. |
| **FR-13** | Seabed Texture | GLCM contrast, energy, homogeneity, entropy, gradient variance | Measures statistical difference between candidate and surrounding seabed. |
| **FR-14** | Embedding Context | Cosine distance between target and background embeddings | Computes neural contrast score using frozen CNN/DINO features. |
| **FR-15** | Feature Extraction | Consolidate 32-dimensional contact feature vector | Generates unified JSON and tabular feature row per candidate contact. |
| **FR-16** | LightGBM Fusion | Gradient boosted decision trees on tabular feature vector | Predicts class probabilities with SHAP values explaining top 5 contributing features. |
| **FR-17** | Calibration | Isotonic regression / Platt scaling | Expected Calibration Error (ECE) $< 0.05$ on held-out validation dataset. |
| **FR-18** | Triage Logic | Categorize into High Confidence, Review, or Natural | Routes contacts to operator queue based on calibrated thresholds. |
| **FR-19** | Geolocation | Ray-tracing from vehicle GPS + heading + slant range to WGS84 | Estimates lat/lon with accuracy circle or outputs `UNAVAILABLE` if metadata missing. |
| **FR-20** | Evidence Card UI | Interactive visual card with crop, profile, SHAP bars, review buttons | Renders complete evidence dossier in frontend; allows 1-click review submission. |
| **FR-21** | Active Learning | Log review decisions into versioned annotation registry | Enables triggered retraining of LightGBM fusion model. |

---

## 7. Mathematical Specifications & Core Formulations

### 7.1 Acoustic Shadow Height Estimation
When towfish altitude $H_a$ (meters) and slant range $R_s$ (meters) are known, the physical target height $h_t$ is computed from the acoustic shadow length $L_s$ (meters):
$$h_t = \frac{H_a \cdot L_s}{R_s + L_s}$$

### 7.2 Anomaly Scoring (PatchCore Memory Bank)
Given patch embedding $z \in \mathbb{R}^D$ from intermediate feature map and coreset memory bank $\mathcal{M}$:
$$s(z) = \min_{m \in \mathcal{M}} \| z - m \|_2$$
The image/crop anomaly score is the maximum patch score re-weighted by neighborhood density:
$$S_{\text{anomaly}} = \max_{z} s(z) \cdot \left( 1 - \frac{\exp(\|z - m^*\|_2)}{\sum_{m \in \mathcal{N}_k(m^*)} \exp(\|z - m\|_2)} \right)$$

### 7.3 Multi-Ping Persistence Ratio
For a contact track initiated at ping $t_0$ and ending at $t_k$, with total potential observations $N_{\text{total}} = t_k - t_0 + 1$ and actual detections $N_{\text{obs}}$:
$$\text{Persistence Ratio} = \frac{N_{\text{obs}}}{N_{\text{total}}}$$

### 7.4 Probability Calibration (Platt Scaling)
Given uncalibrated fusion logit $f(x) = \log \frac{p}{1-p}$:
$$P(\text{Anthropogenic} \mid x) = \frac{1}{1 + \exp(A \cdot f(x) + B)}$$
where parameters $A, B$ are optimized via negative log-likelihood on an out-of-fold validation split.

---

## 8. Definition of Done (DoD)

- [ ] Complete dataset provenance registry with licensing and synthetic flags.
- [ ] Leakage-free train/validation/test splits split strictly by survey site/track.
- [ ] Deterministic preprocessing and quality control pipeline implemented and tested.
- [ ] Multi-detector discovery engine (Classical + PatchCore + RT-DETR/YOLOv8) functional.
- [ ] Physics verification engine (Highlight + Shadow + Collinearity) verified on test suite.
- [ ] Multi-ping Kalman tracker with Hungarian assignment operational.
- [ ] Concentric seabed context feature extractor functional.
- [ ] 32-feature vector generator and LightGBM fusion model trained and validated.
- [ ] Calibration pipeline with ECE evaluation curves generated.
- [ ] REST API endpoints (FastAPI) and async task worker operational.
- [ ] React/Next.js GIS dashboard with Leaflet, Evidence Cards, and SHAP visualizations.
- [ ] Complete end-to-end integration test passing on synthetic and real survey files.
