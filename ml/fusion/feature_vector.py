from typing import Dict, List, Any, Optional
import numpy as np
from ml.discovery.classical_proposal import CandidateProposal
from ml.acoustic.physics_engine import AcousticPhysicsEvidence
from ml.acoustic.filament_analyzer import FilamentEvidence
from ml.tracking.kalman_tracker import ContactTrack
from ml.context.context_engine import SeabedContextEvidence

class FeatureVectorAssembler:
    """
    Consolidates heterogeneous discovery, acoustic physics, filament, temporal,
    contextual, and spatial evidence into a standardized 32-D feature vector.
    """

    FEATURE_NAMES = [
        "classical_conf",
        "patchcore_anomaly",
        "detector_conf",
        "detector_class_id",
        "proposal_source_cnt",
        "highlight_present",
        "highlight_mean_int",
        "highlight_peak_int",
        "highlight_area_px",
        "highlight_aspect_ratio",
        "shadow_present",
        "shadow_darkness",
        "shadow_length_m",
        "estimated_height_m",
        "collinearity_score",
        "grazing_angle_deg",
        "filament_density",
        "mesh_periodicity_index",
        "boundary_tortuosity",
        "is_net_like",
        "track_length",
        "persistence_ratio",
        "pos_residual_rms",
        "velocity_consistency",
        "glcm_contrast_diff",
        "glcm_homogeneity_diff",
        "glcm_energy_diff",
        "glcm_entropy_diff",
        "gradient_var_diff",
        "embedding_dist_ring",
        "seabed_roughness",
        "slant_range_m"
    ]

    CLASS_MAP = {
        "unknown": 0,
        "pipeline": 1,
        "shipwreck": 2,
        "naval_mine": 3,
        "revetment_wall": 4,
        "ghost_net": 5
    }

    @classmethod
    def assemble(
        cls,
        proposal: CandidateProposal,
        physics: AcousticPhysicsEvidence,
        filament: FilamentEvidence,
        track: Optional[ContactTrack] = None,
        context: Optional[SeabedContextEvidence] = None,
        slant_range_m: float = 30.0,
        altitude_m: float = 10.0,
        metadata_quality: int = 1
    ) -> Dict[str, float]:
        """
        Returns an exact, typed dictionary of 32 features.
        """
        # Discovery features
        classical_conf = proposal.confidence if "classical_cv" in proposal.sources else 0.0
        patchcore_anomaly = proposal.anomaly_score if "patchcore_anomaly" in proposal.sources else 0.0
        det_conf = proposal.detector_conf
        det_class_id = float(cls.CLASS_MAP.get(proposal.detector_class, 0))
        source_cnt = float(len(proposal.sources))

        # Temporal features
        if track is not None:
            track_length = float(track.hits)
            persistence = float(track.persistence_ratio)
            pos_residual = float(track.position_residual_rms)
            vel_consistency = 0.95 if track.status == "CONFIRMED" else 0.60
        else:
            track_length = 1.0
            persistence = 1.0
            pos_residual = 0.1
            vel_consistency = 0.50

        # Context features
        if context is not None:
            c_contrast = context.glcm_contrast_diff
            c_homo = context.glcm_homogeneity_diff
            c_energy = context.glcm_energy_diff
            c_entropy = context.glcm_entropy_diff
            c_grad_var = context.gradient_var_diff
            c_embed = context.embedding_cosine_distance
            c_roughness = context.seabed_roughness
        else:
            c_contrast = 10.0
            c_homo = 0.2
            c_energy = 0.1
            c_entropy = 0.5
            c_grad_var = 15.0
            c_embed = 0.3
            c_roughness = 20.0

        features = {
            "classical_conf": float(classical_conf),
            "patchcore_anomaly": float(patchcore_anomaly),
            "detector_conf": float(det_conf),
            "detector_class_id": float(det_class_id),
            "proposal_source_cnt": float(source_cnt),
            
            "highlight_present": 1.0 if physics.highlight_present else 0.0,
            "highlight_mean_int": float(physics.highlight_mean_intensity),
            "highlight_peak_int": float(physics.highlight_peak_intensity),
            "highlight_area_px": float(physics.highlight_area_px),
            "highlight_aspect_ratio": float(physics.highlight_aspect_ratio),
            
            "shadow_present": 1.0 if physics.shadow_present else 0.0,
            "shadow_darkness": float(physics.shadow_darkness),
            "shadow_length_m": float(physics.shadow_length_m),
            "estimated_height_m": float(physics.estimated_target_height_m),
            "collinearity_score": float(physics.collinearity_score),
            "grazing_angle_deg": float(physics.grazing_angle_deg),
            
            "filament_density": float(filament.filament_density),
            "mesh_periodicity_index": float(filament.mesh_periodicity_index),
            "boundary_tortuosity": float(filament.boundary_tortuosity),
            "is_net_like": 1.0 if filament.is_net_like else 0.0,
            
            "track_length": float(track_length),
            "persistence_ratio": float(persistence),
            "pos_residual_rms": float(pos_residual),
            "velocity_consistency": float(vel_consistency),
            
            "glcm_contrast_diff": float(c_contrast),
            "glcm_homogeneity_diff": float(c_homo),
            "glcm_energy_diff": float(c_energy),
            "glcm_entropy_diff": float(c_entropy),
            "gradient_var_diff": float(c_grad_var),
            "embedding_dist_ring": float(c_embed),
            "seabed_roughness": float(c_roughness),
            "slant_range_m": float(slant_range_m)
        }

        return features

    @classmethod
    def to_numpy_array(cls, features: Dict[str, float]) -> np.ndarray:
        return np.array([features[name] for name in cls.FEATURE_NAMES], dtype=np.float32)
