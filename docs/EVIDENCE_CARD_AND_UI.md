# ABYSSEYE — Evidence Card UI & GIS Mission Dashboard Specification

**Document Version:** v3.0  
**Target:** SIH 2026 Problem Statement 26057  
**Module Path:** `frontend/`

---

## 1. UI Architecture & Design Principles

The ABYSSEYE interface is a high-performance, dark-mode-first mission control system built with **Next.js (App Router), Tailwind CSS, Lucide Icons, and Leaflet GIS**.

### 1.1 Core Layout Structure

```
+──────────────────────────────────────────────────────────────────────────────────────────+
|  [ABYSSEYE LOGO]   Survey: Baltic-North-04   | Track: Line-02 | QC: EXCELLENT | Alerts (3)|
+────────────────────────────────────────┬─────────────────────────────────────────────────+
|                                        |                                                 |
|          GIS MISSION MAP               |              CONTACT EVIDENCE CARD              |
|                                        |                                                 |
|  • Bathymetric Base Layer              |  • Contact ID: CONT-2026-0927-00142             |
|  • Survey Tracklines (Polyline)        |  • Triage Status: [ REVIEW ]                    |
|  • Sonar Swath Coverage (Polygon)      |  • Calibrated P(Anthropogenic): 81.2%           |
|  • Geolocated Contact Markers          |                                                 |
|    - Red: High-Confidence (>0.80)      |  ┌───────────────────┬───────────────────────┐  |
|    - Amber: Review Queue (0.40–0.80)   |  │ Raw Waterfall     │ Acoustic Profile Plot │  |
|    - Gray: Natural Seabed (<0.40)      |  │ [ High-res Crop ] │ [ Highlight - Shadow ]│  |
|                                        |  └───────────────────┴───────────────────────┘  |
|  • Navigation Controls & Measurement   |                                                 |
|  • Debris Density Heatmap Overlay      |  • Evidence Chain Checklist:                    |
|                                        |    [x] Acoustic Anomaly: 0.91 (PatchCore)       |
|                                        |    [x] Highlight Detected (Peak: 242)           |
|                                        |    [x] Beam Collinear Shadow (6.8m, 0.94 score) |
|                                        |    [x] Temporal Persistence (7/8 pings)         |
|                                        |    [x] Seabed Context Contrast (GLCM Delta: 48) |
|                                        |    [?] Object Subtype: Unknown Net-like         |
|                                        |                                                 |
|                                        |  • SHAP Attribution Breakdown (Top 5 Features)  |
|                                        |    Shadow Length       [=========+0.42]         |
|                                        |    Collinearity        [========+0.38]          |
|                                        |    Persistence         [======+0.31]            |
|                                        |    Context GLCM        [====+0.18]              |
|                                        |                                                 |
|                                        |  • Operator Triage Action:                      |
|                                        |    [ CONFIRM DEBRIS ] [ NATURAL SEABED ] [UNCERTAIN]
+────────────────────────────────────────┴─────────────────────────────────────────────────+
|  CONTACT TRIAGE QUEUE (Live Data Table with Sortable Filters, Badges & Mini-Thumbnails)  |
+──────────────────────────────────────────────────────────────────────────────────────────+
```

---

## 2. Evidence Card Component Hierarchy

The Evidence Card (`frontend/src/components/EvidenceCard.tsx`) exposes every link of the evidence chain to give the marine operator full auditability:

1. **Header & Decision Triage:**
   - Contact ID and Survey ID.
   - Status Badge (`HIGH_CONFIDENCE`, `REVIEW`, `NATURAL_SEABED`).
   - Calibrated Probability Gauge ($P_{\text{anthro}}$, $P_{\text{natural}}$, $P_{\text{uncertain}}$).
2. **Visual Evidence Inspector:**
   - Synchronized side-by-side viewer: Raw Waterfall vs. Highlight/Shadow Overlay vs. Anomaly Heatmap.
   - 1D Acoustic Cross-Section Profile (Intensity vs Range along beam vector).
3. **Physical & Geometric Dimensions:**
   - Slant Range ($R_s$), Altitude ($H_a$), Grazing Angle ($\theta_g$).
   - Estimated Target Height ($h_t$) with confidence bounds.
4. **SHAP Feature Importance Bar Chart:**
   - Real-time waterfall bar plot showing positive and negative contributors to the LightGBM decision.
5. **Human-in-the-Loop Action Bar:**
   - 1-Click buttons to label as `Anthropogenic`, `Natural`, or `Uncertain`.
   - Subtype selector (`Ghost Net`, `Pipeline`, `Shipwreck`, `Naval Mine`, `Other`).
   - Textarea for operator log notes.
