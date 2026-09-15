# ABYSSEYE — Dataset Strategy & Scientific Provenance Protocol

**Document Version:** v3.0  
**Target:** SIH 2026 Problem Statement 26057  
**Module Path:** `data/`

---

## 1. Scientific Honesty & Dataset Ground Truth Protocol

A core scientific imperative of the ABYSSEYE project is absolute transparency regarding dataset provenance and capabilities:

1. **No Public Real Ghost-Net SSS Benchmark Exists:** Real side-scan sonar datasets with verified ground-truth annotations for discarded fishing nets and ghost gear are virtually absent from the open scientific literature.
2. **Synthetic Data is Strictly a Development & Testing Proxy:** Synthetic sonar simulations (e.g., SAGAR synthetic ghost nets, procedural simulator nets) are strictly flagged as `synthetic: true`. They are utilized for controlled geometry validation, physics ray-tracing tests, and pipeline stress-testing. **Synthetic metrics are never reported as real-world debris detection metrics.**
3. **Optical Marine Debris is Incompatible:** Optical RGB underwater imagery datasets (e.g., TrashCan, DeepSolaris) have fundamentally different propagation physics, scattering dynamics, and resolutions compared to side-scan sonar and are never substituted as SSS ground truth.
4. **Open-Set Anomaly Framing:** Ghost nets and unclassified debris are explicitly surfaced as `UNKNOWN / NET-LIKE ANOMALY` or `ANTHROPOGENIC (UNSPECIFIED)` rather than forcing an artificial classifier decision.

---

## 2. Dataset Taxonomy & Provenance Registry

Every dataset utilized in ABYSSEYE is formally registered in `data/registry/provenance.yaml` with explicit metadata tracking license, real/synthetic status, sensor specifications, and split boundaries.

### 2.1 Supported Benchmark Datasets

```yaml
# data/registry/provenance.yaml sample structure

datasets:
  - id: "subpipe-v1"
    name: "SubPipe Subsea Pipeline Sonar Benchmark"
    modality: "Side-Scan Sonar (SSS)"
    target_classes: ["pipeline", "free_span", "joint"]
    real_data: true
    synthetic: false
    sensor_frequency_khz: 900
    license: "CC-BY-4.0"
    source_url: "https://zenodo.org/records/subpipe"
    usage: ["known_detector_training", "tracking_benchmark"]

  - id: "ai4shipwrecks-sss"
    name: "AI4Shipwrecks Marine Sonar Dataset"
    modality: "Side-Scan Sonar (SSS)"
    target_classes: ["shipwreck", "debris_field"]
    real_data: true
    synthetic: false
    sensor_frequency_khz: 455
    license: "Open Data Commons / CC-BY"
    usage: ["known_detector_training", "physics_verification"]

  - id: "swdd-mines-v2"
    name: "Sonar Water Debris & Mine Benchmark (MILCO-NOMBO)"
    modality: "High-Frequency SSS"
    target_classes: ["naval_mine", "cylinder", "wedge"]
    real_data: true
    synthetic: false
    sensor_frequency_khz: 1200
    license: "Research-Only"
    usage: ["known_detector_training", "contact_benchmark"]

  - id: "benthic-seabed-cat"
    name: "BenthiCat Seafloor Morphology Dataset"
    modality: "Side-Scan Sonar (SSS)"
    target_classes: ["sand_ripples", "rocky_reef", "mud_flat", "posidonia_meadow"]
    real_data: true
    synthetic: false
    sensor_frequency_khz: 455
    license: "CC-BY-SA-4.0"
    usage: ["patchcore_normal_seabed_training", "context_benchmark"]

  - id: "sagar-synthetic-nets"
    name: "SAGAR Simulated Ghost Net Benchmark"
    modality: "Simulated SSS"
    target_classes: ["ghost_net", "trawl_net"]
    real_data: false
    synthetic: true
    sensor_frequency_khz: 900
    license: "GPL-3.0"
    usage: ["simulation_validation", "physics_ray_tracing_stress_test"]
```

---

## 3. Data Leakage Prevention Protocol

Data leakage is a fatal flaw in sonar machine learning due to spatial autocorrelation between adjacent pings and continuous waterfall strips. ABYSSEYE enforces strict isolation rules:

```
                            ALL RAW SURVEYS
                                   │
             ┌─────────────────────┴─────────────────────┐
             ▼                                           ▼
   SURVEY 01 to SURVEY 18                      SURVEY 19 to SURVEY 24
   (Geographic Zone Alpha)                     (Geographic Zone Beta)
             │                                           │
             ▼                                           ▼
  ┌──────────────────────┐                    ┌──────────────────────┐
  │ TRAIN / VAL SPLIT    │                    │ HELD-OUT TEST SPLIT  │
  │ • PatchCore Normals  │                    │ • Zero ping overlap  │
  │ • Detector Training  │                    │ • Unseen seabed type │
  │ • LightGBM Folds     │                    │ • Pure benchmark eval│
  └──────────────────────┘                    └──────────────────────┘
```

### 3.1 Partitioning Rules
1. **Survey-Level Split:** Data is split strictly by entire survey mission / geographic location. Never randomly split individual tiles or crops from the same waterfall.
2. **Track-Line Isolation:** Adjacent overlapping swath lines (within $200\text{m}$ radius) are kept within the same partition.
3. **Temporal Window Isolation:** Multi-ping sequences are assigned to splits as contiguous multi-ping blocks; no ping from a test track is ever accessible during training or validation.
4. **Coreset Isolation:** PatchCore feature memory banks $\mathcal{M}$ are constructed exclusively from training partition background frames.

---

## 4. Unified Data Loader Specification

The unified dataset loader `ml/ingestion/dataset_loader.py` provides a standardized Python generator interface regardless of underlying file structure:

```python
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import numpy as np

@dataclass
class SonarFrameRecord:
    frame_id: str
    survey_id: str
    ping_index: int
    image_array: np.ndarray  # Shape (H, W), dtype uint8 or float32
    slant_range_m: float
    altitude_m: Optional[float]
    heading_deg: Optional[float]
    latitude: Optional[float]
    longitude: Optional[float]
    channel: str  # 'PORT', 'STARBOARD', 'DUAL'
    provenance: Dict[str, Any]  # Dataset ID, real/synthetic flag, license
```
