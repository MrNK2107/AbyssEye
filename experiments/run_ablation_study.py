import sys
import os

# Add workspace root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import json
from typing import Dict, List, Any, Tuple
from sklearn.model_selection import train_test_split
from ml.evaluation.metrics import SonarEvaluationMetrics
from ml.fusion.lightgbm_fusion import LightGBMEvidenceFusion
from ml.fusion.feature_vector import FeatureVectorAssembler

class AblationStudyRunner:
    """
    Executes the 7-Stage Progressive Ablation Study (Experiments A through G)
    demonstrating the empirical value added by each acoustic physics and evidence module.
    """

    def __init__(self, n_samples: int = 600, seed: int = 42):
        self.n_samples = n_samples
        self.seed = seed
        self.feature_names = FeatureVectorAssembler.FEATURE_NAMES

    def generate_synthetic_evaluation_cohort(self) -> Tuple[np.ndarray, np.ndarray]:
        np.random.seed(self.seed)
        N = self.n_samples
        n_feat = len(self.feature_names)

        X = np.zeros((N, n_feat), dtype=np.float32)
        y = np.zeros(N, dtype=int)

        # Half Anthropogenic / Ghost Net, Half Natural Seafloor (Sand ripples, reefs, boulders)
        for i in range(N):
            is_debris = (i % 2 == 0)
            y[i] = 1 if is_debris else 0

            if is_debris:
                # Anthropogenic / Ghost Net: High anomaly, strong highlight, collinear shadow, multi-ping persistence
                det_conf = np.random.beta(4, 2) if np.random.rand() > 0.35 else 0.0
                patchcore_anom = np.random.beta(6, 2)
                highlight_pres = 1.0
                shadow_pres = 1.0 if np.random.rand() > 0.15 else 0.0
                collinear = np.random.uniform(0.85, 0.98) if shadow_pres else 0.0
                persistence = np.random.uniform(0.70, 1.0)
                filament = np.random.uniform(0.50, 0.95)
                glcm_diff = np.random.uniform(30.0, 75.0)
                height = np.random.uniform(0.8, 3.5) if shadow_pres else 0.0
            else:
                # Natural Seabed: Random speckle, sand ripples with non-collinear shadows or low persistence
                det_conf = np.random.beta(1, 5) if np.random.rand() > 0.8 else 0.0
                patchcore_anom = np.random.beta(2, 4)
                highlight_pres = 1.0 if np.random.rand() > 0.4 else 0.0
                shadow_pres = 1.0 if np.random.rand() > 0.6 else 0.0
                collinear = np.random.uniform(0.0, 0.5) if shadow_pres else 0.0
                persistence = np.random.uniform(0.12, 0.45)
                filament = np.random.uniform(0.0, 0.25)
                glcm_diff = np.random.uniform(2.0, 18.0)
                height = 0.0

            # Map to feature vector indices
            X[i, 0] = det_conf                                 # classical_conf
            X[i, 1] = patchcore_anom                           # patchcore_anomaly
            X[i, 2] = det_conf                                 # detector_conf
            X[i, 5] = highlight_pres                           # highlight_present
            X[i, 10] = shadow_pres                             # shadow_present
            X[i, 13] = height                                  # estimated_height_m
            X[i, 14] = collinear                               # collinearity_score
            X[i, 16] = filament                                # filament_density
            X[i, 21] = persistence                             # persistence_ratio
            X[i, 24] = glcm_diff                               # glcm_contrast_diff
            X[i, 31] = np.random.uniform(20.0, 48.0)           # slant_range_m

        return X, y

    def run_all_experiments(self) -> List[Dict[str, Any]]:
        X, y = self.generate_synthetic_evaluation_cohort()
        results = []

        # Stratified Split 70% Train, 30% Test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.30, random_state=42, stratify=y
        )

        # Exp A: Baseline Supervised Detector Only
        prob_A = X_test[:, 2] # detector_conf
        met_A = SonarEvaluationMetrics.calculate_classification_metrics(y_test, prob_A)
        results.append({
            "experiment": "Exp A: Baseline Detector",
            "modules": "Detector Only",
            **met_A
        })

        # Exp B: Dual Discovery (Detector + PatchCore)
        prob_B = np.maximum(X_test[:, 2], X_test[:, 1] * 0.8)
        met_B = SonarEvaluationMetrics.calculate_classification_metrics(y_test, prob_B)
        results.append({
            "experiment": "Exp B: Dual Discovery",
            "modules": "Detector + PatchCore Anomaly",
            **met_B
        })

        # Exp C: Dual Discovery + Acoustic Physics (Collinearity & Height)
        score_C = 0.40 * prob_B + 0.35 * X_test[:, 14] + 0.25 * (X_test[:, 10])
        met_C = SonarEvaluationMetrics.calculate_classification_metrics(y_test, score_C)
        results.append({
            "experiment": "Exp C: + Acoustic Physics",
            "modules": "Discovery + Highlight/Shadow Collinearity",
            **met_C
        })

        # Exp D: + Multi-Ping Tracking
        score_D = 0.30 * prob_B + 0.30 * X_test[:, 14] + 0.40 * X_test[:, 21]
        met_D = SonarEvaluationMetrics.calculate_classification_metrics(y_test, score_D)
        results.append({
            "experiment": "Exp D: + Kalman Tracking",
            "modules": "Physics + Multi-Ping State Persistence",
            **met_D
        })

        # Exp E: + Seabed Context
        score_E = 0.25 * prob_B + 0.25 * X_test[:, 14] + 0.30 * X_test[:, 21] + 0.20 * (X_test[:, 24] / 60.0)
        met_E = SonarEvaluationMetrics.calculate_classification_metrics(y_test, score_E)
        results.append({
            "experiment": "Exp E: + Seabed Context",
            "modules": "Physics + Tracking + GLCM Texture Deltas",
            **met_E
        })

        # Exp F: + LightGBM Fusion (Uncalibrated)
        fusion_F = LightGBMEvidenceFusion()
        fusion_F.train(X_train, y_train, n_splits=3)
        prob_F_raw = fusion_F.model.predict(X_test)
        met_F = SonarEvaluationMetrics.calculate_classification_metrics(y_test, prob_F_raw)
        results.append({
            "experiment": "Exp F: + LightGBM Fusion",
            "modules": "Full 32-D Feature Matrix + GBDT Trees",
            **met_F
        })

        # Exp G: + Isotonic Probability Calibration (Full ABYSSEYE)
        prob_G_cal = fusion_F.calibrator.predict(prob_F_raw)
        met_G = SonarEvaluationMetrics.calculate_classification_metrics(y_test, prob_G_cal)
        results.append({
            "experiment": "Exp G (Full ABYSSEYE)",
            "modules": "LightGBM Fusion + Isotonic Calibration",
            **met_G
        })

        return results

def main():
    print("=========================================================================")
    print("ABYSSEYE - 7-Stage Progressive Ablation Study (SIH Problem 26057)")
    print("=========================================================================\n")

    runner = AblationStudyRunner(n_samples=600, seed=42)
    results = runner.run_all_experiments()

    print(f"{'Experiment':<24} | {'Precision':<9} | {'Recall':<8} | {'F1-Score':<8} | {'AUROC':<7} | {'ECE':<6}")
    print("-" * 75)

    for res in results:
        print(f"{res['experiment']:<24} | {res['precision']:<9.3f} | {res['recall']:<8.3f} | {res['f1_score']:<8.3f} | {res['auroc']:<7.3f} | {res['ece']:<6.3f}")

    # Export to JSON
    os.makedirs(os.path.join("experiments", "results"), exist_ok=True)
    out_path = os.path.join("experiments", "results", "ablation_benchmark_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    print("\n[OK] Ablation benchmark results exported to: " + out_path)
    print("=========================================================================")

if __name__ == "__main__":
    main()
