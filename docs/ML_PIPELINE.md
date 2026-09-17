# ABYSSEYE — Machine Learning & Acoustic Physics Pipeline Specification

**Document Version:** v3.0  
**Target:** SIH 2026 Problem Statement 26057  
**Module Path:** `ml/`

---

## 1. Pipeline Overview

The ABYSSEYE Machine Learning pipeline transforms uncalibrated side-scan sonar waterfall data into calibrated, physics-verified contact predictions through 8 sequential stages:

```
[Raw Sonar Ping] 
   ──▶ [Stage 1: Preprocessing & Slant-Range Correction]
   ──▶ [Stage 2: Multi-Source Candidate Discovery]
   ──▶ [Stage 3: Acoustic Physics Verification]
   ──▶ [Stage 4: Multi-Ping Kalman State Tracking]
   ──▶ [Stage 5: Multi-Scale Seabed Context Analysis]
   ──▶ [Stage 6: 32-D Evidence Vector Consolidation]
   ──▶ [Stage 7: LightGBM Gradient Boosted Fusion]
   ──▶ [Stage 8: Isotonic Probability Calibration & SHAP]
```

---

## 2. Stage 1: Preprocessing & Slant-Range Ground Correction

### 2.1 Slant-Range to Ground-Range Transformation
Side-scan sonar records echo time delays (slant range $R_s$). Given towfish altitude $H_a$ above the seabed, the horizontal ground range $Y_g$ from the nadir path is calculated by the Pythagorean relation:

$$Y_g = \sqrt{R_s^2 - H_a^2} \quad \text{for } R_s \ge H_a$$

Pixels where $R_s < H_a$ represent the **water column blind zone** and are masked or excised.

```
       Towfish (Altitude Ha)
       ●──────────────────┐
       │ \                │
       │   \ Slant Range  │
    Ha │     \ Rs         │
       │       \          │
       ▼─────────●────────▼
     Nadir    Ground Range (Yg)
```

### 2.2 Local Contrast & Speckle Filtering
1. **Intensity Compression:** Apply log-scale compression followed by robust percentile clipping (1st to 99th percentile):
   $$I_{\text{norm}}(x, y) = \frac{\log(1 + I(x, y)) - \log(1 + P_{01})}{\log(1 + P_{99}) - \log(1 + P_{01})}$$
2. **Speckle Attenuation:** Use Enhanced Lee or Bilateral filtering to preserve edge sharpness of acoustic shadows while smoothing Rayleigh speckle noise in uniform seabed zones.

---

## 3. Stage 2: Candidate Contact Discovery

Candidate discovery employs three complementary paradigms to maximize candidate recall ($\ge 95\%$):

```
                       ┌────────────────────────────────┐
                       │ Preprocessed Sonar Waterfall   │
                       └───────────────┬────────────────┘
                                       │
            ┌──────────────────────────┼──────────────────────────┐
            ▼                          ▼                          ▼
 ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
 │ (A) Classical CV     │  │ (B) PatchCore Anomaly│  │ (C) Supervised Detector│
 │  Adaptive Otsu +     │  │  WideResNet50 Coreset│  │  RT-DETR / YOLOv8    │
 │  Morphological Blobs │  │  Feature Memory Bank │  │  (Pipelines, Wrecks) │
 └──────────┬───────────┘  └──────────┬───────────┘  └──────────┬───────────┘
            │                          │                          │
            └──────────────────────────┼──────────────────────────┘
                                       ▼
                       ┌────────────────────────────────┐
                       │  Multi-Source Non-Max Merge    │
                       │    (IoU Gating & BBox Union)   │
                       └────────────────────────────────┘
```

### 3.1 (A) Classical Computer Vision Proposal Engine
- **Local Background Modeling:** Compute local moving window mean $\mu_L(x, y)$ and standard deviation $\sigma_L(x, y)$ over a kernel of size $K \times K$ ($K=64\text{ px}$).
- **Adaptive Thresholding:** Pixels with $I(x, y) > \mu_L(x, y) + k_{\text{high}} \cdot \sigma_L(x, y)$ are flagged as highlights.
- **Morphological Filtering:** Apply morphological closing with an elliptical structuring element ($3 \times 3$) followed by connected components labeling. Bounding boxes with area $A \in [15, 2500]\text{ px}$ are extracted as candidate regions.

### 3.2 (B) PatchCore Feature-Memory Anomaly Engine
PatchCore learns a memory bank of normal seabed representations without requiring positive debris labels.
1. **Feature Extraction:** Sonar patches are passed through a frozen ImageNet-pretrained WideResNet50 backbone. Intermediate feature maps from Layer 2 and Layer 3 are extracted:
   $$\phi(x, y) = \text{Concat}(\text{Layer}_2(x, y), \text{Layer}_3(x, y)) \in \mathbb{R}^{D}$$
2. **Coreset Reduction:** To enable real-time inference ($<20\text{ms}$), greedy $k$-center coreset subsampling reduces the feature memory bank $\mathcal{M}$ to $10\%$ of its original size while preserving minimax Euclidean coverage:
   $$\mathcal{M} = \text{GreedyCoreset}(\mathcal{F}_{\text{normal}}, \text{fraction}=0.10)$$
3. **Patch Anomaly Scoring:**
   $$s(p) = \min_{m \in \mathcal{M}} \|\phi(p) - m\|_2$$
   Dense 2D anomaly heatmaps $A(x, y)$ are smoothed with a Gaussian kernel ($\sigma = 4$), and local maxima above threshold $\tau_{\text{anomaly}} = 0.65$ produce bounding box proposals.

### 3.3 (C) Supervised Known-Object Detector
- Architecture: RT-DETR / YOLOv8x trained on validated SSS benchmarks.
- Classes: `pipeline`, `shipwreck`, `naval_mine`, `revetment_wall`.
- Output: Class label $c$, confidence score $p_{\text{det}} \in [0, 1]$, and bounding box $[x, y, w, h]$.

---

## 4. Stage 3: Acoustic Physics Verification

Every candidate contact is interrogated against the physical principles of underwater acoustic propagation.

```
       Sound Propagation Vector (Beam Angle theta)
       =====================================================>
       ┌──────────────┐
       │  HIGHLIGHT   │========> [ ACOUSTIC SHADOW ]
       │ (High Return)│          (No acoustic return behind object)
       └──────────────┘
```

### 4.1 Highlight & Shadow Segmentation
1. **Highlight Region ($H$):** Segmented via Otsu thresholding on the candidate crop.
   - Peak intensity: $I_{\text{peak}} = \max_{(x, y) \in H} I(x, y)$
   - Mean contrast: $C_{\text{high}} = \frac{\bar{I}_H - \mu_{\text{local}}}{\sigma_{\text{local}}}$
2. **Shadow Region ($S$):** Ray-traced outward along the sonar transmission vector from the highlight centroid:
   $$S = \{(x, y) \mid I(x, y) < \mu_{\text{local}} - 1.5\sigma_{\text{local}}, \text{dist}((x, y), H) \le R_{\max}\}$$
   - Shadow darkness: $D_{\text{shadow}} = 1.0 - \frac{\bar{I}_S}{\mu_{\text{local}}}$
   - Shadow length: $L_s$ (measured in meters).

### 4.2 Collinearity & Geometric Sanity Checks
- **Collinearity Vector:** The vector from highlight centroid $\mathbf{c}_H$ to shadow centroid $\mathbf{c}_S$ must align with the sonar beam propagation unit vector $\hat{\mathbf{v}}_{\text{beam}}$:
  $$\cos \theta_{\text{align}} = \frac{(\mathbf{c}_S - \mathbf{c}_H) \cdot \hat{\mathbf{v}}_{\text{beam}}}{\|\mathbf{c}_S - \mathbf{c}_H\|}$$
  $$\text{Collinearity Score} = \max(0, \cos \theta_{\text{align}})$$
- **Target Height Estimation:**
  $$h_t = \frac{H_a \cdot L_s}{R_s + L_s}$$
  If $h_t \in [0.1\text{m}, 8.0\text{m}]$, the contact exhibits physical height consistent with marine debris.

---

## 5. Stage 4: Multi-Ping Kalman State Tracking

A genuine seabed object persists across consecutive sonar pings. The tracking module maintains temporal consistency.

### 5.1 Discrete Kalman Filter State Space
- **State Vector:** $\mathbf{x}_k = [x_k, y_k, \dot{x}_k, \dot{y}_k, w_k, h_k]^T$
- **State Transition Matrix $\mathbf{F}$:**
  $$\mathbf{F} = \begin{bmatrix} 1 & 0 & \Delta t & 0 & 0 & 0 \\ 0 & 1 & 0 & \Delta t & 0 & 0 \\ 0 & 0 & 1 & 0 & 0 & 0 \\ 0 & 0 & 0 & 1 & 0 & 0 \\ 0 & 0 & 0 & 0 & 1 & 0 \\ 0 & 0 & 0 & 0 & 0 & 1 \end{bmatrix}$$
- **Measurement Matrix $\mathbf{H}$:** $\mathbf{z}_k = [x_m, y_m, w_m, h_m]^T$

### 5.2 Hungarian Data Association & Track Gating
Cost matrix between track $i$ and detection $j$ combines Mahalanobis distance and visual embedding cosine distance:
$$C_{ij} = \alpha \cdot d_{\text{Mahalanobis}}(\mathbf{x}_i, \mathbf{z}_j) + (1 - \alpha) \cdot (1 - \cos(\mathbf{e}_i, \mathbf{e}_j))$$
Tracks with gating cost $C_{ij} > C_{\max}$ are rejected.

### 5.3 Temporal Persistence Metric
$$\text{Persistence Ratio} = \frac{N_{\text{observed}}}{N_{\text{window}}}$$
where $N_{\text{window}}$ is the sliding ping window size (default $N_{\text{window}} = 8$).

---

## 6. Stage 5: Multi-Scale Seabed Context Analysis

To distinguish debris from surrounding natural seabed morphology (sand dunes, rocky reefs), ABYSSEYE extracts concentric spatial context rings:

```
  ┌──────────────────────────────────────────────┐
  │  GLOBAL SEABED CONTEXT (4W x 4H)            │
  │   ┌──────────────────────────────────────┐   │
  │   │  LOCAL RING CONTEXT (2W x 2H)        │   │
  │   │   ┌──────────────────────────────┐   │   │
  │   │   │   TARGET CROP (W x H)        │   │   │
  │   │   │   [ Candidate Contact ]      │   │   │
  │   │   └──────────────────────────────┘   │   │
  │   └──────────────────────────────────────┘   │
  └──────────────────────────────────────────────┘
```

### 6.1 Gray-Level Co-occurrence Matrix (GLCM) Texture Features
For both the target crop $T$ and the surrounding local ring $R$, compute GLCM at angles $\theta \in \{0^\circ, 45^\circ, 90^\circ, 135^\circ\}$ and distance $d=1$:
1. **Contrast:** $\sum_{i, j} |i - j|^2 p(i, j)$
2. **Dissimilarity:** $\sum_{i, j} |i - j| p(i, j)$
3. **Homogeneity:** $\sum_{i, j} \frac{p(i, j)}{1 + |i - j|^2}$
4. **Energy (ASM):** $\sum_{i, j} p(i, j)^2$
5. **Entropy:** $-\sum_{i, j} p(i, j) \log_2(p(i, j) + \epsilon)$

Compute feature delta: $\Delta \text{Contrast} = |\text{Contrast}(T) - \text{Contrast}(R)|$.

### 6.2 Deep Embedding Cosine Distance
Pass Target $T$ and Ring $R$ through a lightweight CNN feature extractor (ResNet18):
$$\text{Context Dissimilarity} = 1 - \frac{\mathbf{f}(T) \cdot \mathbf{f}(R)}{\|\mathbf{f}(T)\|_2 \|\mathbf{f}(R)\|_2}$$

---

## 7. Stage 6: Consolidated 32-Dimensional Feature Vector

The table below details all 32 numerical/categorical features passed into the LightGBM fusion model:

| # | Feature Name | Domain | Type | Description |
|---|---|---|---|---|
| 1 | `classical_conf` | Discovery | float [0, 1] | Normalized contrast confidence from classical detector |
| 2 | `patchcore_anomaly` | Discovery | float [0, 1] | Peak normalized patch anomaly score |
| 3 | `detector_conf` | Discovery | float [0, 1] | Supervised detector confidence (0.0 if unknown) |
| 4 | `detector_class_id`| Discovery | int [0, 5] | Encoded class (0: None, 1: Pipe, 2: Wreck, 3: Mine, 4: Wall) |
| 5 | `proposal_source_cnt`| Discovery | int [1, 3] | Number of proposal engines discovering this contact |
| 6 | `highlight_present` | Physics | binary {0, 1} | Acoustic highlight detected |
| 7 | `highlight_mean_int`| Physics | float [0, 255]| Mean highlight pixel intensity |
| 8 | `highlight_peak_int`| Physics | float [0, 255]| Maximum highlight pixel intensity |
| 9 | `highlight_area_px` | Physics | int | Number of pixels in highlight segment |
| 10 | `highlight_aspect_ratio`| Physics| float | Ratio of highlight major to minor axis |
| 11 | `shadow_present` | Physics | binary {0, 1} | Acoustic shadow detected along propagation vector |
| 12 | `shadow_darkness` | Physics | float [0, 1] | Relative darkness of shadow vs surrounding seabed |
| 13 | `shadow_length_m` | Physics | float $\ge 0$ | Shadow length converted to ground meters |
| 14 | `estimated_height_m`| Physics | float $\ge 0$ | Triangulated target height from shadow formula |
| 15 | `collinearity_score`| Physics | float [0, 1] | Cosine similarity between beam vector & shadow vector |
| 16 | `grazing_angle_deg` | Physics | float [0, 90] | Acoustic incidence angle at target slant range |
| 17 | `track_length` | Temporal | int $\ge 1$ | Total sequential pings this contact has been tracked |
| 18 | `persistence_ratio`| Temporal | float [0, 1] | Ratio of observed pings to total track window |
| 19 | `pos_residual_rms` | Temporal | float $\ge 0$ | Kalman filter positional error residual (meters) |
| 20 | `velocity_consistency`| Temporal| float [0, 1] | Track velocity consistency (stationary vs moving target) |
| 21 | `area_variance` | Temporal | float $\ge 0$ | Variance of contact bounding box area across pings |
| 22 | `glcm_contrast_diff`| Context | float $\ge 0$ | Difference in GLCM contrast: Target vs Local Ring |
| 23 | `glcm_homogeneity_diff`| Context| float [0, 1]| Difference in GLCM homogeneity: Target vs Local Ring |
| 24 | `glcm_energy_diff` | Context | float [0, 1] | Difference in GLCM energy: Target vs Local Ring |
| 25 | `glcm_entropy_diff`| Context | float $\ge 0$ | Difference in GLCM entropy: Target vs Local Ring |
| 26 | `gradient_var_diff`| Context | float $\ge 0$ | Difference in Sobel gradient variance: Target vs Ring |
| 27 | `embedding_dist_ring`| Context | float [0, 2] | Cosine distance of ResNet feature: Target vs Ring |
| 28 | `embedding_dist_global`| Context| float [0, 2] | Cosine distance of ResNet feature: Target vs Global |
| 29 | `seabed_roughness` | Context | float $\ge 0$ | Standard deviation of background seabed intensity |
| 30 | `slant_range_m` | Spatial | float $\ge 0$ | Distance from sonar transducer to target |
| 31 | `altitude_m` | Spatial | float $\ge 0$ | Vehicle altitude above seabed |
| 32 | `metadata_quality` | Spatial | int [0, 2] | 0: None, 1: Partial, 2: Full GPS + Heading |

---

## 8. Stage 7 & 8: LightGBM Fusion, Calibration & Explainability

### 8.1 LightGBM Hyperparameter Configuration
```python
LIGHTGBM_PARAMS = {
    "objective": "multiclass",
    "num_class": 3,  # 0: Natural, 1: Anthropogenic, 2: Uncertain
    "boosting_type": "gbdt",
    "learning_rate": 0.03,
    "num_leaves": 31,
    "max_depth": 5,
    "min_child_samples": 20,
    "subsample": 0.85,
    "colsample_bytree": 0.80,
    "reg_alpha": 0.1,
    "reg_lambda": 1.0,
    "n_estimators": 350,
    "random_state": 42
}
```

### 8.2 Probability Calibration (Isotonic Regression)
Raw LightGBM probabilities are calibrated using 5-fold cross-validation isotonic regression models:
$$P_{\text{calibrated}} = g(P_{\text{raw}})$$
Minimizes Expected Calibration Error (ECE):
$$\text{ECE} = \sum_{m=1}^{M} \frac{|B_m|}{N} \left| \text{acc}(B_m) - \text{conf}(B_m) \right| < 0.04$$

### 8.3 Explainability via TreeSHAP
For every classified contact, SHAP values $\phi_i$ satisfy the additive feature attribution property:
$$f(x) = \phi_0 + \sum_{i=1}^{32} \phi_i(x)$$
The top 5 positive and negative contributing features are packaged into the Contact Digital Twin for operator review.
