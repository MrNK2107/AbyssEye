# ABYSSEYE — Active Learning & Contact Annotation Benchmark

**Document Version:** v3.0  
**Target:** SIH 2026 Problem Statement 26057  
**Module Path:** `ml/active_learning/` & `data/contacts/`

---

## 1. The Contact Annotation Benchmark

Because public datasets lack labeled real-world ghost-net instances, ABYSSEYE establishes a standardized, contact-level ground-truth benchmark ($N \ge 1,000$ contacts) to train, calibrate, and evaluate the LightGBM fusion model.

### 1.1 Ground Truth Annotation Taxonomy

```
                          CONTACT LABEL
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
   ANTHROPOGENIC             NATURAL                UNCERTAIN
  ┌───────────────┐     ┌───────────────┐      ┌────────────────┐
  │ • PIPELINE    │     │ • SAND_RIPPLE │      │ • AMBIGUOUS    │
  │ • SHIPWRECK   │     │ • ROCKY_REEF  │      │ • LOW_SNR      │
  │ • NAVAL_MINE  │     │ • BOULDER     │      │ • DEGRADED_PING│
  │ • REVETMENT   │     │ • BIOLOGICAL  │      └────────────────┘
  │ • GHOST_NET   │     │ • FLAT_MUD    │
  │ • UNKNOWN_MAN │     └───────────────┘
  └───────────────┘
```

---

## 2. Active Learning Feedback Loop

Rather than annotating uninformative background regions, active learning prioritizes samples that maximize gradient updates and resolve model ambiguity.

```
       ┌────────────────────────────────────────────────────────┐
       │             Raw Sonar Survey Processing                │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │     Candidate Discovery & LightGBM Inference           │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │           Active Learning Prioritization Queue         │
       │   1. High Anomaly + Low Detector Confidence            │
       │   2. Maximum Entropy / Uncertainty: P(Anth) ~ 0.50     │
       │   3. Conflicting Physics: High Highlight, Low Shadow   │
       │   4. Novel Seabed Clusters (Embedding Outliers)        │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │          Operator 1-Click Human-in-the-Loop            │
       │          Review & Evidence Card Confirmation           │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │          Versioned Contact Registry Update             │
       │               (data/contacts/v3.0.parquet)             │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │           Triggered LightGBM Retraining                │
       │            + Out-of-Fold Re-Calibration                │
       └────────────────────────────────────────────────────────┘
```

### 2.1 Priority Sampling Acquisition Functions
1. **Uncertainty Sampling (Shannon Entropy):**
   $$H(x) = - \sum_{c \in \{\text{Anth}, \text{Nat}, \text{Unc}\}} P(c \mid x) \log_2 P(c \mid x)$$
2. **Detector-Anomaly Disagreement:**
   $$\text{Disagreement}(x) = |S_{\text{patchcore}}(x) - P_{\text{detector}}(x)|$$
3. **Seabed Representation Diversity:** Density-based sampling in ResNet embedding space to sample under-represented seafloor textures.
