import pytest
import numpy as np

from ml.context.context_engine import SeabedContextEngine, SeabedContextEvidence
from ml.fusion.feature_vector import FeatureVectorAssembler
from ml.discovery.classical_proposal import CandidateProposal
from ml.acoustic.physics_engine import AcousticPhysicsEvidence
from ml.acoustic.filament_analyzer import FilamentEvidence
from ml.tracking.kalman_tracker import ContactTrack

def test_seabed_context_engine():
    H, W = 128, 256
    canvas = np.random.uniform(90, 130, (H, W)).astype(np.uint8)
    # Insert high contrast texture target
    canvas[50:70, 100:130] = 235

    engine = SeabedContextEngine()
    bbox = (100, 50, 30, 20)
    evidence = engine.analyze_context(canvas, bbox)

    assert isinstance(evidence, SeabedContextEvidence)
    assert evidence.glcm_contrast_diff > 0.0
    assert evidence.isolation_score > 0.0

def test_feature_vector_assembler():
    prop = CandidateProposal(
        proposal_id="P1",
        bbox=(100, 50, 30, 20),
        centroid=(115.0, 60.0),
        confidence=0.89,
        sources=["classical_cv", "patchcore_anomaly"],
        area_px=600,
        mean_intensity=210.0,
        peak_intensity=245.0,
        aspect_ratio=1.5,
        anomaly_score=0.91
    )

    phys = AcousticPhysicsEvidence(
        highlight_present=True,
        highlight_mean_intensity=210.0,
        highlight_peak_intensity=245.0,
        highlight_area_px=600,
        highlight_aspect_ratio=1.5,
        shadow_present=True,
        shadow_darkness=0.82,
        shadow_length_m=6.5,
        shadow_area_px=450,
        estimated_target_height_m=1.75,
        collinearity_score=0.94,
        grazing_angle_deg=18.5,
        physical_consistency_score=0.92
    )

    fil = FilamentEvidence(
        filament_density=0.65,
        mesh_periodicity_index=0.48,
        boundary_tortuosity=2.4,
        is_net_like=True
    )

    context = SeabedContextEvidence(
        glcm_contrast_diff=35.0,
        glcm_homogeneity_diff=0.4,
        glcm_energy_diff=0.2,
        glcm_entropy_diff=0.6,
        gradient_var_diff=45.0,
        embedding_cosine_distance=0.55,
        seabed_roughness=22.0,
        isolation_score=0.85
    )

    features = FeatureVectorAssembler.assemble(
        proposal=prop,
        physics=phys,
        filament=fil,
        context=context,
        slant_range_m=35.0,
        altitude_m=12.0
    )

    assert len(features) == 32
    assert len(FeatureVectorAssembler.FEATURE_NAMES) == 32
    for k, v in features.items():
        assert isinstance(v, (float, int))
        assert not np.isnan(v)

    arr = FeatureVectorAssembler.to_numpy_array(features)
    assert arr.shape == (32,)
