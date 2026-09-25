import numpy as np
from typing import Dict, List, Tuple, Any
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    brier_score_loss
)

class SonarEvaluationMetrics:
    """
    Comprehensive evaluation metrics for SSS debris detection, candidate recall,
    and probability calibration reliability.
    """

    @staticmethod
    def calculate_classification_metrics(y_true: np.ndarray, y_pred_prob: np.ndarray, threshold: float = 0.50) -> Dict[str, float]:
        y_pred = (y_pred_prob >= threshold).astype(int)

        precision = float(precision_score(y_true, y_pred, zero_division=0))
        recall = float(recall_score(y_true, y_pred, zero_division=0))
        f1 = float(f1_score(y_true, y_pred, zero_division=0))

        try:
            auroc = float(roc_auc_score(y_true, y_pred_prob))
        except Exception:
            auroc = 0.50

        try:
            auprc = float(average_precision_score(y_true, y_pred_prob))
        except Exception:
            auprc = float(np.mean(y_true))

        brier = float(brier_score_loss(y_true, y_pred_prob))
        ece = SonarEvaluationMetrics.expected_calibration_error(y_true, y_pred_prob)

        return {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "auroc": round(auroc, 4),
            "auprc": round(auprc, 4),
            "brier_score": round(brier, 4),
            "ece": round(ece, 4)
        }

    @staticmethod
    def expected_calibration_error(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
        """
        Calculates Expected Calibration Error (ECE):
        ECE = sum_m (|B_m| / N) * |acc(B_m) - conf(B_m)|
        """
        bin_boundaries = np.linspace(0, 1, n_bins + 1)
        ece = 0.0
        n_samples = len(y_true)

        for i in range(n_bins):
            bin_lower = bin_boundaries[i]
            bin_upper = bin_boundaries[i + 1]

            in_bin = (y_prob > bin_lower) & (y_prob <= bin_upper)
            prop_in_bin = np.mean(in_bin)

            if prop_in_bin > 0:
                accuracy_in_bin = np.mean(y_true[in_bin])
                avg_confidence_in_bin = np.mean(y_prob[in_bin])
                ece += np.abs(accuracy_in_bin - avg_confidence_in_bin) * prop_in_bin

        return float(ece)

    @staticmethod
    def calculate_false_alarms_per_km(
        false_positives: int,
        total_pings: int,
        ping_interval_m: float = 0.10
    ) -> float:
        """Calculates false alarms per linear kilometer of survey line."""
        total_distance_km = (total_pings * ping_interval_m) / 1000.0
        if total_distance_km <= 0:
            return 0.0
        return float(false_positives / total_distance_km)
