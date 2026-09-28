import os
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import json
import base64
import cv2

from ml.ingestion.sonar_parser import SonarParser, SonarFrameRecord
from ml.ingestion.quality_control import QualityControlEngine, QCReport
from ml.preprocessing.filters import SonarFilterEngine
from ml.preprocessing.slant_range import SlantRangeCorrector
from ml.discovery.classical_proposal import ClassicalProposalEngine, CandidateProposal
from ml.discovery.patchcore_anomaly import PatchCoreAnomalyDetector
from ml.discovery.proposal_fusion import ProposalFusionEngine
from ml.acoustic.physics_engine import AcousticPhysicsEngine, AcousticPhysicsEvidence
from ml.acoustic.filament_analyzer import GhostNetFilamentAnalyzer, FilamentEvidence
from ml.tracking.kalman_tracker import MultiPingKalmanTracker, ContactTrack
from ml.context.context_engine import SeabedContextEngine, SeabedContextEvidence
from ml.fusion.feature_vector import FeatureVectorAssembler
from ml.fusion.lightgbm_fusion import LightGBMEvidenceFusion, CalibratedFusionDecision
from ml.geolocation.georeference import SonarGeoreferencer

class PipelineOrchestrator:
    """
    End-to-End Master Execution Pipeline for ABYSSEYE.
    Coordinates all 8 processing stages to transform raw sonar data into
    calibrated, physics-verified Contact Digital Twins.
    """

    def __init__(self, models_dir: str = "models"):
        self.qc_engine = QualityControlEngine()
        self.classical_engine = ClassicalProposalEngine(k_sigma=1.6, min_area_px=15)
        self.patchcore_engine = PatchCoreAnomalyDetector(patch_size=16, stride=8, anomaly_threshold=0.55)
        self.physics_engine = AcousticPhysicsEngine(pixel_res_m=0.05)
        self.filament_analyzer = GhostNetFilamentAnalyzer()
        self.tracker = MultiPingKalmanTracker(max_dist_gating_px=60.0, confirm_hits_threshold=2)
        self.context_engine = SeabedContextEngine()
        
        self.models_dir = models_dir
        model_path = os.path.join(models_dir, "lightgbm_fusion_latest.joblib")
        if os.path.exists(model_path):
            self.fusion_model = LightGBMEvidenceFusion(model_path=model_path)
        else:
            self.fusion_model = LightGBMEvidenceFusion()

    def _extract_crop_base64(self, image: np.ndarray, bbox: Tuple[int, int, int, int], margin: int = 40) -> str:
        """Extracts a bounded crop around the target and converts to Base64 PNG."""
        H, W = image.shape
        x, y, w, h = bbox
        
        x0 = max(0, x - margin)
        y0 = max(0, y - margin)
        x1 = min(W, x + w + margin * 2) # Extra margin for shadow extension
        y1 = min(H, y + h + margin)

        crop = image[y0:y1, x0:x1]
        if crop.size == 0:
            return ""

        # Normalize to uint8 grayscale
        crop_uint8 = np.clip(crop, 0, 255).astype(np.uint8)
        success, encoded_img = cv2.imencode('.png', crop_uint8)
        if not success:
            return ""

        b64_str = base64.b64encode(encoded_img.tobytes()).decode('utf-8')
        return f"data:image/png;base64,{b64_str}"

    def _extract_beam_profile(
        self,
        image: np.ndarray,
        centroid: Tuple[float, float],
        nadir_col: int,
        profile_len: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Extracts 1D acoustic intensity profile along the sonar ray-trace axis
        from pre-target seafloor through highlight peak into acoustic shadow.
        """
        H, W = image.shape
        cx, cy = int(centroid[0]), int(centroid[1])
        cy = max(0, min(H - 1, cy))

        direction = 1 if cx >= nadir_col else -1
        start_x = cx - (direction * 15)  # 15px before target (ambient seabed)
        end_x = cx + (direction * (profile_len - 15)) # through shadow

        profile_data = []
        for i in range(profile_len):
            sample_x = start_x + (direction * i)
            sample_x = max(0, min(W - 1, sample_x))
            intensity = int(image[cy, sample_x])
            
            # Determine region tag
            if i < 15:
                region = "AMBIENT_SEABED"
            elif 15 <= i < 25:
                region = "HIGHLIGHT_PEAK"
            elif 25 <= i < 50:
                region = "ACOUSTIC_SHADOW"
            else:
                region = "SEABED_RECOVERY"

            dist_offset_m = round((i - 15) * 0.05, 2)
            profile_data.append({
                "sample_idx": i,
                "range_offset_m": dist_offset_m,
                "intensity": intensity,
                "region": region
            })

        return profile_data

    def process_frame(
        self,
        frame_record: SonarFrameRecord,
        ping_index: int = 0
    ) -> Tuple[QCReport, List[Dict[str, Any]]]:
        raw_img = frame_record.image_array
        # Normalize ultra-high-resolution imagery to standard SSS processing grid
        if raw_img.shape[1] > 1024 or raw_img.shape[0] > 768:
            scale_w = 768 / raw_img.shape[1]
            scale_h = 384 / raw_img.shape[0]
            raw_img = cv2.resize(raw_img, (768, 384), interpolation=cv2.INTER_AREA)

        H, W = raw_img.shape
        nadir_col = W // 2

        # Stage 1: Quality Control
        qc_report = self.qc_engine.evaluate(raw_img, altitude_m=frame_record.altitude_m)
        if qc_report.status == "CORRUPTED":
            return qc_report, []

        # Stage 2: Preprocessing
        preprocessed = SonarFilterEngine.preprocess_pipeline(raw_img)

        # Stage 3: Multi-Source Discovery
        classical_props = self.classical_engine.detect_proposals(preprocessed, frame_id=frame_record.frame_id)
        patchcore_props = self.patchcore_engine.detect_proposals(preprocessed, frame_id=frame_record.frame_id)
        
        all_raw_props = classical_props + patchcore_props
        fused_props = ProposalFusionEngine.fuse_proposals(all_raw_props, iou_threshold=0.30)
        # Keep top-4 highest confidence candidates to keep UI clean and responsive
        fused_props = sorted(fused_props, key=lambda p: p.confidence, reverse=True)[:4]

        # Stage 4: Multi-Ping Kalman Tracking
        active_tracks = self.tracker.update(fused_props, ping_index=ping_index)

        contacts_digital_twins = []

        for idx, prop in enumerate(fused_props):
            # Stage 5: Acoustic Physics Verification & Filament Netting Signature
            physics_ev = self.physics_engine.analyze_contact(
                full_image=preprocessed,
                bbox=prop.bbox,
                nadir_col=nadir_col,
                altitude_m=frame_record.altitude_m or 10.0,
                max_slant_range_m=frame_record.slant_range_m
            )

            # Crop target for filament analysis
            px, py, pw, ph = prop.bbox
            crop_target = preprocessed[py:py+ph, px:px+pw]
            filament_ev = self.filament_analyzer.analyze_patch(crop_target)

            # Stage 6: Seabed Context Analysis
            context_ev = self.context_engine.analyze_context(preprocessed, prop.bbox)

            # Match to tracking state
            matched_track = active_tracks[idx] if idx < len(active_tracks) else None

            # Calculate across-track distance
            dist_from_nadir_px = abs(prop.centroid[0] - nadir_col)
            across_track_m = (dist_from_nadir_px / (W / 2.0)) * frame_record.slant_range_m
            is_starboard = (prop.centroid[0] >= nadir_col)

            # Stage 7: Feature Vector Assembly & Calibrated LightGBM Fusion
            feature_dict = FeatureVectorAssembler.assemble(
                proposal=prop,
                physics=physics_ev,
                filament=filament_ev,
                track=matched_track,
                context=context_ev,
                slant_range_m=frame_record.slant_range_m,
                altitude_m=frame_record.altitude_m or 10.0
            )

            fusion_decision = self.fusion_model.predict(feature_dict)

            # Accurate, contextual target subtype hint
            p_anth = getattr(fusion_decision, "p_anthropogenic", 0.85)
            if fusion_decision.triage_state == "HIGH_CONFIDENCE" or p_anth > 0.65:
                if filament_ev.is_net_like or filament_ev.filament_density > 0.35:
                    target_hint = "GHOST_NET"
                elif "pipeline" in str(prop.detector_class).lower():
                    target_hint = "PIPELINE"
                elif "wreck" in str(prop.detector_class).lower() or physics_ev.estimated_target_height_m > 1.2:
                    target_hint = "SHIPWRECK"
                else:
                    target_hint = "MARINE_DEBRIS"
            elif fusion_decision.triage_state == "REVIEW" or p_anth > 0.30:
                if filament_ev.is_net_like:
                    target_hint = "SUSPECTED_NET"
                else:
                    target_hint = "ACOUSTIC_ANOMALY"
            else:
                target_hint = "NATURAL_SEABED"

            # Stage 8: Geolocation Ray-Tracing
            geo_info = SonarGeoreferencer.calculate_contact_coordinates(
                vessel_lat=frame_record.latitude or 54.8210,
                vessel_lon=frame_record.longitude or 18.7340,
                heading_deg=frame_record.heading_deg or 180.0,
                across_track_m=across_track_m,
                is_starboard=is_starboard
            )

            contact_id = f"CONT-{frame_record.survey_id}-{frame_record.ping_index:03d}-{idx+1:02d}"

            # Extract real acoustic image crop and 1D beam profile
            crop_b64 = self._extract_crop_base64(preprocessed, prop.bbox)
            beam_profile = self._extract_beam_profile(preprocessed, prop.centroid, nadir_col)

            # Assemble Contact Digital Twin
            contact_twin = {
                "contact_id": contact_id,
                "survey_id": frame_record.survey_id,
                "frame_id": frame_record.frame_id,
                "ping_index": frame_record.ping_index,
                "bbox": list(prop.bbox),
                "centroid": [round(float(prop.centroid[0]), 1), round(float(prop.centroid[1]), 1)],
                "channel": "STARBOARD" if is_starboard else "PORT",
                "triage_state": fusion_decision.triage_state,
                "target_type_hint": target_hint,
                
                "spatial_telemetry": {
                    **geo_info,
                    "altitude_m": frame_record.altitude_m or 10.0,
                    "slant_range_m": round(frame_record.slant_range_m, 2),
                    "across_track_m": round(across_track_m, 2),
                    "heading_deg": frame_record.heading_deg or 180.0
                },

                "evidence_graph": {
                    "discovery": {
                        "sources": prop.sources,
                        "confidence": round(float(prop.confidence), 3),
                        "anomaly_score": round(float(prop.anomaly_score), 3)
                    },
                    "acoustic_physics": physics_ev.to_dict(),
                    "filament_netting": filament_ev.to_dict(),
                    "seabed_context": context_ev.to_dict(),
                    "temporal_tracking": matched_track.to_dict() if matched_track else None
                },

                "fusion_decision": fusion_decision.to_dict(),
                "feature_vector": feature_dict,
                "crop_image_base64": crop_b64,
                "beam_profile": beam_profile,

                "human_review": {
                    "reviewed_by": None,
                    "review_timestamp": None,
                    "decision": None,
                    "notes": None
                }
            }

            contacts_digital_twins.append(contact_twin)

        return qc_report, contacts_digital_twins
