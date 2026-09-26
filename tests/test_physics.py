import pytest
import numpy as np

from ml.acoustic.physics_engine import AcousticPhysicsEngine, AcousticPhysicsEvidence
from ml.acoustic.filament_analyzer import GhostNetFilamentAnalyzer, FilamentEvidence
from ml.ingestion.synthetic_generator import SyntheticSonarGenerator

def test_acoustic_physics_engine():
    gen = SyntheticSonarGenerator(height_pings=128, width_cols=256, altitude_m=10.0, max_slant_range_m=40.0)
    canvas = gen.generate_seabed_background(seabed_type="sand_ripples", seed=42)
    # Insert target with target height = 2.0m at column 180 (starboard)
    canvas, meta = gen.insert_target(canvas, target_type="ghost_net", center_ping=64, center_col=180, target_height_m=2.0)

    engine = AcousticPhysicsEngine(pixel_res_m=0.05)
    bbox = (meta["bbox"][0], meta["bbox"][1], meta["bbox"][2], meta["bbox"][3])
    evidence = engine.analyze_contact(
        full_image=canvas,
        bbox=bbox,
        nadir_col=128,
        altitude_m=10.0,
        max_slant_range_m=40.0
    )

    assert isinstance(evidence, AcousticPhysicsEvidence)
    assert evidence.highlight_present is True
    assert evidence.shadow_present is True
    assert evidence.collinearity_score > 0.8
    assert evidence.estimated_target_height_m > 0.5  # Reconstructed target height

def test_ghost_net_filament_analyzer():
    analyzer = GhostNetFilamentAnalyzer()

    # 1. Test on mesh/net-like patch with periodic striations
    net_patch = np.zeros((48, 48), dtype=np.uint8)
    for y in range(48):
        for x in range(48):
            if (x % 4 == 0) or (y % 4 == 0):
                net_patch[y, x] = 240
            else:
                net_patch[y, x] = 160

    net_ev = analyzer.analyze_patch(net_patch)
    assert net_ev.filament_density > 0.20
    assert net_ev.mesh_periodicity_index > 0.15

    # 2. Test on flat uniform patch
    flat_patch = np.full((48, 48), 120, dtype=np.uint8)
    flat_ev = analyzer.analyze_patch(flat_patch)
    assert flat_ev.filament_density < 0.10
    assert flat_ev.is_net_like is False
