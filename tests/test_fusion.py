import pytest
import numpy as np
import os
import tempfile

from ml.fusion.lightgbm_fusion import LightGBMEvidenceFusion, CalibratedFusionDecision
from ml.fusion.feature_vector import FeatureVectorAssembler

def test_lightgbm_train_and_calibrate():
    np.random.seed(42)
    N = 100
    n_features = len(FeatureVectorAssembler.FEATURE_NAMES)
    X = np.random.uniform(0.0, 1.0, (N, n_features)).astype(np.float32)
    # Target label: high anomaly and high collinearity implies anthropogenic
    y = ((X[:, 1] > 0.5) & (X[:, 14] > 0.5)).astype(int)

    fusion = LightGBMEvidenceFusion()
    metrics = fusion.train(X, y, n_splits=3)

    assert "brier_score" in metrics
    assert "accuracy" in metrics
    assert metrics["brier_score"] < 0.35

    # Test prediction on single sample
    sample_dict = {name: float(X[0, i]) for i, name in enumerate(FeatureVectorAssembler.FEATURE_NAMES)}
    decision = fusion.predict(sample_dict)

    assert isinstance(decision, CalibratedFusionDecision)
    assert 0.0 <= decision.p_anthropogenic <= 1.0
    assert 0.0 <= decision.p_natural <= 1.0
    assert 0.0 <= decision.p_uncertain <= 1.0
    total_prob = decision.p_anthropogenic + decision.p_natural + decision.p_uncertain
    assert abs(total_prob - 1.0) < 0.05
    assert len(decision.top_shap_features) > 0
    assert decision.triage_state in ["HIGH_CONFIDENCE", "REVIEW", "NATURAL_SEABED"]

def test_save_and_load_model():
    np.random.seed(42)
    X = np.random.uniform(0.0, 1.0, (50, 32)).astype(np.float32)
    y = (X[:, 0] > 0.5).astype(int)

    fusion = LightGBMEvidenceFusion()
    fusion.train(X, y, n_splits=2)

    with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        fusion.save(tmp_path)
        assert os.path.exists(tmp_path)

        loaded_fusion = LightGBMEvidenceFusion(model_path=tmp_path)
        assert loaded_fusion.model is not None
        assert loaded_fusion.calibrator is not None
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
