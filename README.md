# ABYSSEYE — AI-Powered Automated Underwater Marine Debris and Anomaly Detection System using Side-Scan Sonar Imagery

[![SIH 2026](https://img.shields.io/badge/SIH%202026-Problem%2026057-0284c7.svg)](https://smartindiahackathon.gov.in)
[![Technical Baseline](https://img.shields.io/badge/Architecture-v3.0%20Enhanced-10b981.svg)](docs/PRD_v3.0.md)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

> **Official Implementation Baseline for Smart India Hackathon (SIH) 2026 — Problem Statement 26057**

---

## 🌊 Executive Summary & Core Differentiator

**ABYSSEYE** is an open-set, physics-verified Side-Scan Sonar (SSS) contact-analysis engine designed to detect anthropogenic marine debris (including ghost nets, abandoned fishing gear, subsea pipelines, shipwrecks, and naval ordnance) against complex natural seafloor topographies.

Unlike traditional computer-vision pipelines that treat sonar analysis as a simple 2D bounding-box problem (which fails on rare/unlabeled debris classes like ghost nets and suffers from severe false alarms on rocky reefs), **ABYSSEYE builds an end-to-end, multi-modal evidence chain**:

```
Open-set Contact Discovery 
  ➔ Acoustic Physics Verification 
    ➔ Multi-Ping Tracking (Kalman / Hungarian) 
      ➔ Seabed-Context Analysis 
        ➔ 32-D Evidence Representation 
          ➔ Calibrated LightGBM Fusion 
            ➔ Geolocation & Evidence Card Intelligence
```

### 💡 Core Differentiator
> **ABYSSEYE does not classify a sonar pixel in isolation. It evaluates whether a contact behaves like a physical object across acoustic, temporal, contextual, and spatial evidence, then exposes the transparent evidence chain that produced the decision.**

---

## 📑 Comprehensive Documentation Index

All technical specifications, mathematical foundations, and system designs have been comprehensively documented:

| Document | Description |
|---|---|
| 📄 [**PRD v3.0**](docs/PRD_v3.0.md) | Complete Product Requirements Document detailing all 44 sections, functional requirements, and definitions of done. |
| 🏗️ [**System Architecture**](docs/ARCHITECTURE.md) | High-level system architecture, Contact Digital Twin & Evidence Graph schema, and database design. |
| 🧠 [**ML Pipeline & Physics Engine**](docs/ML_PIPELINE.md) | Deep mathematical formulations, PatchCore anomaly scoring, highlight-shadow collinearity, Kalman tracking, and 32-D feature vector specification. |
| 📊 [**Dataset Strategy & Provenance**](docs/DATASET_STRATEGY.md) | Provenance registry, real vs. synthetic data protocol, data leakage prevention, and benchmark datasets. |
| 🔌 [**Backend API Specification**](docs/API_SPECIFICATION.md) | FastAPI REST endpoints, OpenAPI schemas, and WebSocket real-time telemetry stream specifications. |
| 🎛️ [**Evidence Card & GIS Dashboard**](docs/EVIDENCE_CARD_AND_UI.md) | UI/UX specifications for the operator triage interface, Leaflet bathymetric mission map, and SHAP explainability card. |
| 🔁 [**Active Learning & Benchmark**](docs/ACTIVE_LEARNING_AND_BENCHMARK.md) | 1,000+ contact benchmark methodology, annotation taxonomy, acquisition functions, and continuous retraining loop. |
| 🔬 [**Ablation Study Protocol**](docs/ABLATION_STUDY.md) | Research hypotheses H1–H6, 7-stage progressive ablation matrix (Exp A to Exp G), and evaluation metrics. |

---

## 🏛️ System Architecture Flowchart

```
+─────────────────────────────────────────────────────────────────────────+
|                        SONAR DATA INGESTION & QC                        |
|        (XTF, JSF, GeoTIFF, Waterfall Imagery, Slant-Range Logs)        |
+─────────────────────────────────────────────────────────────────────────+
                                     │
                                     ▼
+─────────────────────────────────────────────────────────────────────────+
|                 MULTI-SOURCE CANDIDATE CONTACT DISCOVERY                |
|   ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐  |
|   │ Classical CV     │    │ PatchCore Anomaly│    │ YOLOv8 / RT-DETR │  |
|   │ (Adaptive/Otsu)  │    │ (WideResNet50)   │    │ (Supervised SSS) │  |
|   └────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘  |
|            └───────────────────────┼───────────────────────┘            |
|                                    ▼                                    |
|                      Unified Candidate Region Proposals                 |
+─────────────────────────────────────────────────────────────────────────+
                                     │
                                     ▼
+─────────────────────────────────────────────────────────────────────────+
|                      ACOUSTIC PHYSICS VERIFICATION                      |
|   • Highlight extraction & contrast estimation                          |
|   • Beam-aligned acoustic shadow ray-tracing                            |
|   • Collinearity verification & physical target height estimation       |
+─────────────────────────────────────────────────────────────────────────+
                                     │
                                     ▼
+─────────────────────────────────────────────────────────────────────────+
|                      MULTI-PING STATE ESTIMATION (KALMAN)               |
|   • 2D State tracking across sequential sonar pings                     |
|   • Hungarian assignment with appearance and spatial gating             |
|   • Persistence ratio & trajectory consistency calculation              |
+─────────────────────────────────────────────────────────────────────────+
                                     │
                                     ▼
+─────────────────────────────────────────────────────────────────────────+
|                         SEABED CONTEXT MODULE                           |
|   • Concentric multi-scale crops: [Target] vs [Local Ring] vs [Global]  |
|   • GLCM texture deltas (Contrast, Homogeneity, Energy, Entropy)        |
|   • Neural seabed embedding cosine dissimilarity                        |
+─────────────────────────────────────────────────────────────────────────+
                                     │
                                     ▼
+─────────────────────────────────────────────────────────────────────────+
|                 32-D FEATURE CONSOLIDATION & LIGHTGBM FUSION            |
|   • Tabular feature vector generation across all evidence streams       |
|   • Gradient Boosted Decision Tree (LightGBM) classification            |
|   • TreeSHAP local feature attribution calculations                     |
+─────────────────────────────────────────────────────────────────────────+
                                     │
                                     ▼
+─────────────────────────────────────────────────────────────────────────+
|                         PROBABILITY CALIBRATION                         |
|   • Isotonic Regression & Platt Scaling on out-of-fold validation data  |
|   • Reliable P(Anthropogenic), P(Natural), P(Uncertain) outputs         |
+─────────────────────────────────────────────────────────────────────────+
                                     │
                   ┌─────────────────┴─────────────────┐
                   ▼                                   ▼
+────────────────────────────────────+ +──────────────────────────────────+
|      GIS MISSION CONTROL (Leaflet) | |     PHYSICS EVIDENCE CARD UI     |
| • Bathymetric trackline overlays   | | • High-resolution sonar crops    |
| • Swath polygon coverage           | | • 1D Acoustic beam profile plot  |
| • Geolocated target markers & heat | | • SHAP contribution bar chart    |
+────────────────────────────────────+ +──────────────────────────────────+
                   │                                   │
                   └─────────────────┬─────────────────┘
                                     ▼
+─────────────────────────────────────────────────────────────────────────+
|                    OPERATOR REVIEW & ACTIVE LEARNING                    |
|   • 1-Click contact triage: High Confidence | Review | Natural Seabed   |
|   • Versioned annotation logging & automated retraining queue           |
+─────────────────────────────────────────────────────────────────────────+
```

---

## 📂 Repository Organization

```text
abysseye/
├── docs/                               # Comprehensive Technical Documentation
│   ├── PRD_v3.0.md                     # Product Requirements Document v3.0
│   ├── ARCHITECTURE.md                 # System Architecture & Dataflow
│   ├── ML_PIPELINE.md                  # Machine Learning & Physics Formulations
│   ├── DATASET_STRATEGY.md             # Dataset Provenance & Leakage Rules
│   ├── API_SPECIFICATION.md            # Backend REST & WebSocket API Specs
│   ├── EVIDENCE_CARD_AND_UI.md         # UI/UX & Evidence Card Specs
│   ├── ACTIVE_LEARNING_AND_BENCHMARK.md# Annotation Benchmark & AL Loop
│   └── ABLATION_STUDY.md               # Research Hypotheses & Ablation Matrix
├── backend/                            # FastAPI Python Backend Service
├── frontend/                           # Next.js / Tailwind / Leaflet GIS UI
├── ml/                                 # Machine Learning & CV Modules
│   ├── ingestion/                      # XTF/JSF/GeoTIFF parsers
│   ├── preprocessing/                  # Slant-range ground correction & filters
│   ├── discovery/                      # Classical, PatchCore, and Detectors
│   ├── acoustic/                       # Highlight/Shadow physics & height logic
│   ├── tracking/                       # Multi-ping Kalman tracker & Hungarian
│   ├── context/                        # GLCM texture & embedding distance
│   ├── fusion/                         # 32-D feature vector & LightGBM model
│   ├── calibration/                    # Isotonic regression & Platt scaling
│   ├── geolocation/                    # Sonar ray-tracing to WGS84 coordinates
│   └── evaluation/                     # Metric calculation & ablation runner
├── data/                               # Dataset Registry & Sample Sonar Data
├── models/                             # Serialized weights (LightGBM, PatchCore)
├── experiments/                        # Reproducible ablation experiment scripts
└── tests/                              # Unit & integration test suite
```

---

## 🎯 SIH 2026 Core Principles & Scientific Integrity

1. **Synthetic Data is Not Ground Truth:** Synthetic sonar simulations are strictly utilized for pipeline testing and geometry verification; they are never passed off as real ghost-net benchmarks.
2. **Open-Set Discovery:** Unidentified contacts that exhibit rigid/semi-rigid physical acoustic properties are presented transparently as `UNKNOWN / NET-LIKE ANOMALY` with uncertainty bounds.
3. **No Coordinate Fabrication:** Geolocation relies strictly on genuine navigation logs and acoustic ray-tracing. If telemetry is missing, coordinates are flagged as `UNAVAILABLE`.
4. **Calibrated Probabilities:** Output scores reflect true empirical confidence validated by Expected Calibration Error ($ECE < 0.05$).
