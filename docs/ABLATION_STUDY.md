# ABYSSEYE — Research Hypotheses & Ablation Study Protocol

**Document Version:** v3.0  
**Target:** SIH 2026 Problem Statement 26057  
**Module Path:** `experiments/`

---

## 1. Research Hypotheses

The ABYSSEYE technical architecture is grounded on six testable scientific hypotheses:

- **H1 (Candidate Recall):** Combining Classical CV with learned PatchCore anomaly discovery achieves higher candidate recall on open-set debris than supervised detectors alone ($>95\%$ vs $\sim 78\%$).
- **H2 (Physics Verification):** Acoustic highlight-shadow collinearity and height estimation features reduce natural seabed false alarms per kilometer by $\ge 40\%$.
- **H3 (Multi-Ping Persistence):** Multi-ping Kalman tracking with persistence gating suppresses transient acoustic scattering artifacts and improves contact precision.
- **H4 (Seabed Context):** Concentric GLCM texture deltas and deep embedding distances effectively discriminate man-made structures from complex background seabed formations (sand dunes, rocky reefs).
- **H5 (Learned Evidence Fusion):** A calibrated LightGBM decision tree fusion model significantly outperforms fixed hand-weighted heuristic scoring ($F_1$ gain $\ge 0.12$).
- **H6 (Calibration Reliability):** Isotonic regression calibration reduces Expected Calibration Error (ECE) below $0.05$, providing trustworthy probabilities for marine operators.

---

## 2. 7-Stage Progressive Ablation Matrix

| Config | Stage Description | Discovery | Physics | Tracking | Context | LightGBM Fusion | Calibration |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Exp A** | Baseline Supervised Detector | Detector Only | ✗ | ✗ | ✗ | ✗ (Fixed rule) | ✗ |
| **Exp B** | Dual Discovery | Detector + PatchCore | ✗ | ✗ | ✗ | ✗ (Fixed rule) | ✗ |
| **Exp C** | + Acoustic Physics | Detector + PatchCore | **Yes** | ✗ | ✗ | ✗ (Fixed rule) | ✗ |
| **Exp D** | + Multi-Ping Tracking | Detector + PatchCore | **Yes** | **Yes** | ✗ | ✗ (Fixed rule) | ✗ |
| **Exp E** | + Seabed Context | Detector + PatchCore | **Yes** | **Yes** | **Yes** | ✗ (Fixed rule) | ✗ |
| **Exp F** | + LightGBM Fusion | Detector + PatchCore | **Yes** | **Yes** | **Yes** | **Yes** | ✗ |
| **Exp G (Full)** | + Probability Calibration | Detector + PatchCore | **Yes** | **Yes** | **Yes** | **Yes** | **Yes** |

---

## 3. Evaluation Metrics & Benchmark Dataset Splits

### 3.1 Quantitative Metrics
1. **Candidate Recall (%):** Proportion of true anthropogenic contacts discovered in Stage 2.
2. **Precision, Recall, F1-Score:** Contact-level binary classification at decision threshold $\tau = 0.50$.
3. **AUROC & AUPRC:** Area under ROC and Precision-Recall curves across all confidence thresholds.
4. **False Alarms per km ($\text{FA}/\text{km}$):** Number of natural seabed false positives per linear survey kilometer.
5. **Expected Calibration Error (ECE):**
   $$\text{ECE} = \sum_{m=1}^{M} \frac{|B_m|}{N} |\text{acc}(B_m) - \text{conf}(B_m)|$$
6. **Brier Score:** Mean squared error between calibrated probability and ground-truth binary label.
