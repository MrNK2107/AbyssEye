import pytest
import numpy as np

from ml.discovery.classical_proposal import ClassicalProposalEngine, CandidateProposal
from ml.discovery.patchcore_anomaly import PatchCoreAnomalyDetector
from ml.discovery.proposal_fusion import ProposalFusionEngine
from ml.ingestion.synthetic_generator import SyntheticSonarGenerator

def test_classical_proposal_engine():
    gen = SyntheticSonarGenerator(height_pings=128, width_cols=256, altitude_m=10.0, max_slant_range_m=40.0)
    canvas = gen.generate_seabed_background(seabed_type="sand_ripples", seed=42)
    # Insert prominent target
    canvas, meta = gen.insert_target(canvas, target_type="ghost_net", center_ping=64, center_col=180, target_height_m=1.8)

    engine = ClassicalProposalEngine(k_sigma=1.5, min_area_px=10)
    proposals = engine.detect_proposals(canvas)
    assert len(proposals) > 0

    # Ensure at least one proposal captures the target near (180, 64)
    found_target = False
    for p in proposals:
        cx, cy = p.centroid
        if abs(cx - 180) < 30 and abs(cy - 64) < 30:
            found_target = True
            break
    assert found_target is True

def test_patchcore_anomaly_detector():
    detector = PatchCoreAnomalyDetector(patch_size=16, stride=8, anomaly_threshold=0.50)

    # 1. Fit on normal background
    normal_img = np.random.uniform(90, 130, (128, 128)).astype(np.uint8)
    detector.fit_normal_seabed([normal_img])
    assert detector.memory_bank is not None
    assert len(detector.memory_bank) > 0

    # 2. Test anomaly map on image with anomalous bright patch
    test_img = normal_img.copy()
    test_img[50:70, 50:70] = 250  # Inject strong anomaly

    heatmap, peak_score = detector.compute_anomaly_map(test_img)
    assert heatmap.shape == (128, 128)
    assert peak_score > 0.40

def test_proposal_fusion():
    prop1 = CandidateProposal(
        proposal_id="P1",
        bbox=(50, 50, 30, 30),
        centroid=(65.0, 65.0),
        confidence=0.85,
        sources=["classical_cv"],
        area_px=900,
        mean_intensity=210.0,
        peak_intensity=245.0,
        aspect_ratio=1.0
    )

    prop2 = CandidateProposal(
        proposal_id="P2",
        bbox=(55, 55, 28, 28),
        centroid=(69.0, 69.0),
        confidence=0.92,
        sources=["patchcore_anomaly"],
        area_px=784,
        mean_intensity=215.0,
        peak_intensity=248.0,
        aspect_ratio=1.0,
        anomaly_score=0.92
    )

    fused = ProposalFusionEngine.fuse_proposals([prop1, prop2], iou_threshold=0.3)
    assert len(fused) == 1
    assert "classical_cv" in fused[0].sources
    assert "patchcore_anomaly" in fused[0].sources
    assert fused[0].confidence == 0.92
