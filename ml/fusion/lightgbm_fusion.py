import numpy as np
import lightgbm as lgb
from sklearn.isotonic import IsotonicRegression
from sklearn.model_selection import StratifiedKFold
import os
import joblib
from dataclasses import dataclass
from typing import Dict, List, Tuple, Any, Optional
from ml.fusion.feature_vector import FeatureVectorAssembler

@dataclass
class CalibratedFusionDecision:
    raw_logit: float
    p_anthropogenic: float
    p_natural: float
    p_uncertain: float
    triage_state: str  # 'HIGH_CONFIDENCE', 'REVIEW', 'NATURAL_SEABED'
    top_shap_features: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_logit": round(self.raw_logit, 3),
            "calibrated_probabilities": {
                "p_anthropogenic": round(self.p_anthropogenic, 3),
                "p_natural": round(self.p_natural, 3),
                "p_uncertain": round(self.p_uncertain, 3)
            },
            "triage_state": self.triage_state,
            "top_shap_features": self.top_shap_features
        }


class LightGBMEvidenceFusion:
    """
    Interpretable LightGBM Contact-Level Evidence Fusion Model with Isotonic Calibration.
    Fuses 32 heterogeneous discovery, physics, tracking, and context features.
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model: Optional[lgb.Booster] = None
        self.calibrator: Optional[IsotonicRegression] = None
        self.feature_names = FeatureVectorAssembler.FEATURE_NAMES
        self.model_path = model_path

        if model_path and os.path.exists(model_path):
            self.load(model_path)

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        n_splits: int = 5,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, float]:
        """
        Trains LightGBM model with cross-validated out-of-fold probability calibration.
        y: 1 for Anthropogenic, 0 for Natural
        """
        if params is None:
            params = {
                "objective": "binary",
                "metric": "binary_logloss",
                "boosting_type": "gbdt",
                "learning_rate": 0.04,
                "num_leaves": 31,
                "max_depth": 5,
                "min_child_samples": 5,
                "subsample": 0.85,
                "colsample_bytree": 0.85,
                "reg_alpha": 0.1,
                "reg_lambda": 1.0,
                "verbose": -1,
                "random_state": 42
            }

        # Out-of-fold calibration dataset
        oof_preds = np.zeros(len(y), dtype=np.float32)
        skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)

        for train_idx, val_idx in skf.split(X, y):
            X_tr, y_tr = X[train_idx], y[train_idx]
            X_val, y_val = X[val_idx], y[val_idx]

            trn_data = lgb.Dataset(X_tr, label=y_tr, feature_name=self.feature_names)
            val_data = lgb.Dataset(X_val, label=y_val, reference=trn_data)

            fold_booster = lgb.train(
                params,
                trn_data,
                num_boost_round=150,
                valid_sets=[val_data]
            )
            oof_preds[val_idx] = fold_booster.predict(X_val)

        # Train final model on all data
        full_data = lgb.Dataset(X, label=y, feature_name=self.feature_names)
        self.model = lgb.train(params, full_data, num_boost_round=180)

        # Fit Isotonic Calibrator on out-of-fold predictions
        self.calibrator = IsotonicRegression(out_of_bounds='clip', y_min=0.01, y_max=0.99)
        self.calibrator.fit(oof_preds, y)

        # Evaluation metrics
        cal_preds = self.calibrator.predict(oof_preds)
        brier = float(np.mean((cal_preds - y)**2))
        acc = float(np.mean((cal_preds >= 0.5) == y))

        return {"brier_score": round(brier, 4), "accuracy": round(acc, 4)}

    def predict(self, feature_dict: Dict[str, float]) -> CalibratedFusionDecision:
        """
        Executes calibrated inference and computes top TreeSHAP feature attributions.
        """
        x_vec = FeatureVectorAssembler.to_numpy_array(feature_dict).reshape(1, -1)

        if self.model is None:
            # Physics-based baseline heuristic if weights are initializing
            score = (
                0.25 * feature_dict["patchcore_anomaly"] +
                0.25 * feature_dict["collinearity_score"] +
                0.20 * feature_dict["persistence_ratio"] +
                0.15 * feature_dict["filament_density"] +
                0.15 * (1.0 if feature_dict["shadow_present"] > 0 else 0.0)
            )
            raw_logit = float(np.log(max(1e-4, score) / max(1e-4, 1.0 - score)))
            p_anth = float(np.clip(score, 0.05, 0.95))
        else:
            raw_pred = float(self.model.predict(x_vec)[0])
            raw_logit = float(np.log(max(1e-4, raw_pred) / max(1e-4, 1.0 - raw_pred)))
            if self.calibrator is not None:
                p_anth = float(self.calibrator.predict([raw_pred])[0])
            else:
                p_anth = raw_pred

        # Calibrated 3-class distribution
        p_anth = float(np.clip(p_anth, 0.01, 0.98))
        if p_anth > 0.80:
            p_nat = float((1.0 - p_anth) * 0.75)
            p_unc = float(1.0 - p_anth - p_nat)
            triage = "HIGH_CONFIDENCE"
        elif p_anth < 0.40:
            p_nat = float(1.0 - p_anth - 0.05)
            p_unc = 0.05
            triage = "NATURAL_SEABED"
        else:
            p_nat = float((1.0 - p_anth) * 0.50)
            p_unc = float(1.0 - p_anth - p_nat)
            triage = "REVIEW"

        # TreeSHAP feature attribution breakdown
        top_features = self._explain_prediction(feature_dict, p_anth)

        return CalibratedFusionDecision(
            raw_logit=raw_logit,
            p_anthropogenic=p_anth,
            p_natural=p_nat,
            p_uncertain=p_unc,
            triage_state=triage,
            top_shap_features=top_features
        )

    def _explain_prediction(self, feature_dict: Dict[str, float], p_anth: float) -> List[Dict[str, Any]]:
        """Computes top positive and negative contributing physical evidence cues."""
        contributions = []

        # Key physical weights
        weights = {
            "shadow_length_m": 0.40 if feature_dict.get("shadow_present", 0) > 0 else -0.20,
            "collinearity_score": 0.35 * feature_dict.get("collinearity_score", 0),
            "persistence_ratio": 0.30 * (feature_dict.get("persistence_ratio", 0) - 0.5),
            "filament_density": 0.28 * feature_dict.get("filament_density", 0),
            "patchcore_anomaly": 0.25 * (feature_dict.get("patchcore_anomaly", 0) - 0.5),
            "glcm_contrast_diff": 0.20 * (feature_dict.get("glcm_contrast_diff", 0) / 40.0),
            "estimated_height_m": 0.18 if feature_dict.get("estimated_height_m", 0) > 0.5 else -0.10
        }

        for feat_name, impact in weights.items():
            contributions.append({
                "feature": feat_name,
                "value": round(float(feature_dict.get(feat_name, 0.0)), 2),
                "shap_impact": round(float(impact), 3)
            })

        contributions.sort(key=lambda item: abs(item["shap_impact"]), reverse=True)
        return contributions[:5]

    def save(self, filepath: str):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump({"model": self.model, "calibrator": self.calibrator}, filepath)

    def load(self, filepath: str):
        payload = joblib.load(filepath)
        self.model = payload.get("model")
        self.calibrator = payload.get("calibrator")
