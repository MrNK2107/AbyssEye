import os
import sys
import json
import numpy as np
import cv2
import lightgbm as lgb
from sklearn.isotonic import IsotonicRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import brier_score_loss, roc_auc_score, f1_score, precision_score, recall_score, classification_report
import joblib
from typing import Tuple

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ml.ingestion.synthetic_generator import SyntheticSonarGenerator
from ml.ingestion.dataset_loader import UnifiedDatasetLoader
from ml.ingestion.sonar_parser import SonarParser
from ml.fusion.feature_vector import FeatureVectorAssembler
from backend.app.services.pipeline_orchestrator import PipelineOrchestrator

def generate_multi_source_dataset(
    num_synthetic_surveys: int = 6,
    pings_per_survey: int = 5,
    max_real_samples_per_ds: int = 20
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Assembles a comprehensive multi-source training dataset combining:
      1. Physics-grounded synthetic pings with ground-truth acoustic ray-tracing.
      2. SubPipe real subsea pipeline survey frames.
      3. REMARO-SWDD real debris and obstacle frames.
      4. UMich AI4Shipwrecks real shipwreck frames.
    """
    print("=================================================================")
    print("  ABYSSEYE — Multi-Source (Real + Synthetic) Dataset Assembly   ")
    print("=================================================================")

    orchestrator = PipelineOrchestrator()
    X_features = []
    y_labels = []

    # -------------------------------------------------------------
    # 1. Real Sonar Datasets Ingestion
    # -------------------------------------------------------------
    real_configs = [
        ("SubPipe", "subpipe", "data/raw/subpipe", True),     # Pipelines -> Anthropogenic (1)
        ("SWDD", "swdd", "data/raw/swdd", True),             # Debris/Mines -> Anthropogenic (1)
        ("AI4Shipwrecks", "shipwreck", "data/raw/umich_sonar", True) # Shipwrecks -> Anthropogenic (1)
    ]

    total_real_frames = 0
    for name, dtype, dpath, is_anth in real_configs:
        print(f"Loading real-world sonar frames from {name}...")
        records = list(UnifiedDatasetLoader.stream_dataset_records(dtype, dpath, max_samples=max_real_samples_per_ds))
        for r_idx, rec in enumerate(records):
            total_real_frames += 1
            qc_rep, contacts = orchestrator.process_frame(rec, ping_index=r_idx)
            
            for c in contacts:
                f_dict = c.get("feature_vector", {})
                f_array = FeatureVectorAssembler.to_numpy_array(f_dict)
                # Label based on physical height & collinearity verification
                phys = c.get("evidence_graph", {}).get("acoustic_physics", {})
                collin = phys.get("collinearity_score", 0.0)
                height = phys.get("estimated_target_height_m", 0.0)
                
                # Real anthropogenic debris shows positive height and shadow consistency
                lbl = 1 if (is_anth and (collin > 0.4 or height > 0.3)) else 0
                X_features.append(f_array)
                y_labels.append(lbl)

    print(f"[OK] Ingested {total_real_frames} real-world sonar frames.")

    # -------------------------------------------------------------
    # 2. Synthetic Physics-Grounded Simulations (Ghost nets, seabed)
    # -------------------------------------------------------------
    print("\nGenerating physics-grounded synthetic sonar surveys (ghost nets, sand, rock, mud)...")
    data_dir = os.path.join("data", "training_raw")
    os.makedirs(data_dir, exist_ok=True)

    seafloors = ["sand_ripples", "rocky_reef", "mud_flat"]
    target_types = ["ghost_net", "pipeline", "shipwreck", "ordnance", "natural_boulder"]

    total_syn_frames = 0
    for s_idx in range(num_synthetic_surveys):
        seabed = seafloors[s_idx % len(seafloors)]
        survey_id = f"SRV-TRAIN-{seabed.upper()[:4]}-{s_idx+1:02d}"
        survey_folder = os.path.join(data_dir, survey_id)
        os.makedirs(survey_folder, exist_ok=True)

        gen = SyntheticSonarGenerator(
            height_pings=384,
            width_cols=768,
            altitude_m=10.0 + (s_idx * 1.5),
            max_slant_range_m=50.0
        )

        for p_idx in range(pings_per_survey):
            total_syn_frames += 1
            canvas = gen.generate_seabed_background(seabed_type=seabed, seed=s_idx * 100 + p_idx)
            target_type = target_types[(s_idx + p_idx) % len(target_types)]
            is_anthropogenic = target_type != "natural_boulder"

            target_h = 0.8 + np.random.uniform(0.2, 2.0)
            c_col = int(np.random.choice([gen.width * 0.25, gen.width * 0.75]))
            canvas_with_target, t_meta = gen.insert_target(
                canvas,
                target_type=target_type,
                center_ping=gen.height // 2,
                center_col=c_col,
                target_height_m=target_h
            )

            file_path = os.path.join(survey_folder, f"ping_{p_idx:04d}.png")
            cv2.imwrite(file_path, canvas_with_target)

            rec = SonarParser.load_from_file(
                image_path=file_path,
                survey_id=survey_id,
                ping_index=p_idx,
                altitude_m=gen.altitude_m,
                slant_range_m=gen.max_slant_range_m
            )

            qc_rep, contacts = orchestrator.process_frame(rec, ping_index=p_idx)
            for c in contacts:
                f_dict = c.get("feature_vector", {})
                c_centroid = c.get("centroid", [0, 0])
                dist_to_true_target = np.hypot(c_centroid[0] - c_col, c_centroid[1] - (gen.height // 2))
                
                label = 1 if (is_anthropogenic and dist_to_true_target < 80.0) else 0
                feature_array = FeatureVectorAssembler.to_numpy_array(f_dict)
                X_features.append(feature_array)
                y_labels.append(label)

    X = np.array(X_features, dtype=np.float32)
    y = np.array(y_labels, dtype=np.int32)

    print(f"\n[OK] Assembled complete dataset: {len(X)} contact feature vectors from {total_real_frames + total_syn_frames} sonar frames.")
    print(f"     Class Distribution: {np.sum(y == 1)} Anthropogenic (Positive), {np.sum(y == 0)} Natural (Negative)\n")
    return X, y

def train_and_calibrate_models(X: np.ndarray, y: np.ndarray):
    """
    Trains LightGBM model with 5-fold Stratified Cross-Validation
    and fits out-of-fold Isotonic Regression for Probability Calibration.
    """
    print("=================================================================")
    print("  ABYSSEYE — Training LightGBM Model with Isotonic Calibration   ")
    print("=================================================================")

    feature_names = FeatureVectorAssembler.FEATURE_NAMES
    n_splits = min(5, max(2, int(np.min(np.bincount(y)))))

    params = {
        "objective": "binary",
        "metric": "binary_logloss",
        "boosting_type": "gbdt",
        "learning_rate": 0.05,
        "num_leaves": 31,
        "max_depth": 6,
        "min_child_samples": 3,
        "subsample": 0.85,
        "colsample_bytree": 0.85,
        "reg_alpha": 0.1,
        "reg_lambda": 1.0,
        "verbose": -1,
        "random_state": 42
    }

    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    oof_preds = np.zeros(len(y), dtype=np.float32)

    for fold, (train_idx, val_idx) in enumerate(skf.split(X, y)):
        X_tr, y_tr = X[train_idx], y[train_idx]
        X_val, y_val = X[val_idx], y[val_idx]

        trn_data = lgb.Dataset(X_tr, label=y_tr, feature_name=feature_names)
        val_data = lgb.Dataset(X_val, label=y_val, reference=trn_data)

        booster = lgb.train(
            params,
            trn_data,
            num_boost_round=120,
            valid_sets=[val_data]
        )
        oof_preds[val_idx] = booster.predict(X_val)
        fold_auc = roc_auc_score(y_val, oof_preds[val_idx]) if len(np.unique(y_val)) > 1 else 1.0
        print(f"  • Fold {fold+1}/{n_splits}: Validation ROC-AUC = {fold_auc:.4f}")

    # Train final model on full dataset
    full_dataset = lgb.Dataset(X, label=y, feature_name=feature_names)
    final_booster = lgb.train(params, full_dataset, num_boost_round=150)

    # Fit Isotonic Regression Calibrator on out-of-fold predictions
    print("\nFitting Isotonic Regression Calibrator...")
    calibrator = IsotonicRegression(out_of_bounds='clip', y_min=0.01, y_max=0.99)
    calibrator.fit(oof_preds, y)

    calibrated_preds = calibrator.predict(oof_preds)
    brier = brier_score_loss(y, calibrated_preds)
    roc_auc = roc_auc_score(y, calibrated_preds) if len(np.unique(y)) > 1 else 1.0
    f1 = f1_score(y, (calibrated_preds >= 0.50).astype(int), zero_division=0)
    precision = precision_score(y, (calibrated_preds >= 0.50).astype(int), zero_division=0)
    recall = recall_score(y, (calibrated_preds >= 0.50).astype(int), zero_division=0)

    # Compute Expected Calibration Error (ECE)
    bin_boundaries = np.linspace(0, 1, 11)
    ece = 0.0
    for b in range(len(bin_boundaries) - 1):
        bin_mask = (calibrated_preds >= bin_boundaries[b]) & (calibrated_preds < bin_boundaries[b+1])
        if np.sum(bin_mask) > 0:
            bin_acc = np.mean(y[bin_mask])
            bin_conf = np.mean(calibrated_preds[bin_mask])
            ece += (np.sum(bin_mask) / len(y)) * np.abs(bin_acc - bin_conf)

    print("\n=================================================================")
    print("  MODEL EVALUATION & CALIBRATION METRICS")
    print("=================================================================")
    print(f"  * ROC-AUC Score:                {roc_auc:.4f}")
    print(f"  * Calibrated Brier Score:       {brier:.4f} (Target: < 0.08)")
    print(f"  * Expected Calibration Error:   {ece:.4f} (Target: < 0.05)")
    print(f"  * Macro F1-Score:               {f1:.4f} (Target: > 0.88)")
    print(f"  * Precision:                    {precision:.4f}")
    print(f"  * Recall:                       {recall:.4f}")
    print("=================================================================\n")

    # Serialize Model
    models_dir = "models"
    os.makedirs(models_dir, exist_ok=True)
    out_file = os.path.join(models_dir, "lightgbm_fusion_latest.joblib")
    joblib.dump({"model": final_booster, "calibrator": calibrator, "feature_names": feature_names}, out_file)
    print(f"[OK] Calibrated LightGBM model successfully serialized to: {out_file}")

    # Export Metrics JSON
    results_dir = os.path.join("experiments", "results")
    os.makedirs(results_dir, exist_ok=True)
    metrics_path = os.path.join(results_dir, "training_metrics_report.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump({
            "roc_auc": round(float(roc_auc), 4),
            "brier_score": round(float(brier), 4),
            "expected_calibration_error": round(float(ece), 4),
            "macro_f1": round(float(f1), 4),
            "precision": round(float(precision), 4),
            "recall": round(float(recall), 4),
            "total_samples": len(X),
            "positive_samples": int(np.sum(y == 1)),
            "negative_samples": int(np.sum(y == 0))
        }, f, indent=2)
    print(f"[OK] Metrics report exported to: {metrics_path}")

if __name__ == "__main__":
    X, y = generate_multi_source_dataset(
        num_synthetic_surveys=6,
        pings_per_survey=5,
        max_real_samples_per_ds=20
    )
    train_and_calibrate_models(X, y)
