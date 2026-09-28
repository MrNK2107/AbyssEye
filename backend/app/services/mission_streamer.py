"""
ABYSSEYE: AUV Mission Stream & Real-Time Hydrographic Simulation Engine
SIH 2026 Problem 26057: Automated Underwater Marine Debris Detection

Primary Flagship Demo: Full continuous AUV mission across the UMich AI4Shipwrecks
NOAA Thunder Bay National Marine Sanctuary survey (Iver3 AUV + EdgeTech 2205 SSS).
"""

import os
import sys
import glob
import time
import base64
import zipfile
import asyncio
import logging
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import numpy as np
import cv2

# Project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from ml.ingestion.sonar_parser import SonarParser, SonarFrameRecord
from ml.ingestion.dataset_loader import UnifiedDatasetLoader
from ml.preprocessing.filters import SonarFilterEngine
from ml.preprocessing.slant_range import SlantRangeCorrector
from backend.app.services.pipeline_orchestrator import PipelineOrchestrator

logger = logging.getLogger("MissionStreamer")

@dataclass
class MissionConfig:
    mission_id: str
    title: str
    region: str
    environment: str
    platform: str
    sonar_sensor: str
    origin_lat: float
    origin_lng: float
    nominal_depth_m: float
    nominal_altitude_m: float
    nominal_heading_deg: float
    speed_mps: float
    dataset_type: str
    data_dir: str
    max_pings: int

PRECONFIGURED_MISSIONS = {
    "umich_thunderbay": MissionConfig(
        mission_id="MSN-NOAA-IVER3-THUNDERBAY",
        title="Thunder Bay AUV Sanctuary Mission (UMich AI4Shipwrecks)",
        region="NOAA Thunder Bay National Marine Sanctuary (Lake Huron)",
        environment="Historic Shipwreck Sanctuary • Glacial Lacustrine Bed • EdgeTech 2205 Dual-Freq",
        platform="OceanServer Iver3 AUV",
        sonar_sensor="EdgeTech 2205 High-Resolution Dual-Freq SSS (410/1200 kHz)",
        origin_lat=45.0621,
        origin_lng=-83.4312,
        nominal_depth_m=34.5,
        nominal_altitude_m=12.0,
        nominal_heading_deg=135.0,
        speed_mps=1.54,  # ~3.0 knots
        dataset_type="shipwreck",
        data_dir="data/raw/umich_sonar",
        max_pings=300
    ),
    "baltic_debris": MissionConfig(
        mission_id="MSN-BALTIC-SWDD-01",
        title="Baltic Sea Debris & Munitions Patrol (REMARO SWDD)",
        region="Bornholm Deep Basin (Baltic Sea)",
        environment="Muddy Silt Seabed • Low Ambient Light • Historic Munitions & Plastics",
        platform="OceanScan-MST Light AUV",
        sonar_sensor="Tritech StarFish 450F High-Frequency Sonar",
        origin_lat=55.3214,
        origin_lng=14.8920,
        nominal_depth_m=48.5,
        nominal_altitude_m=11.5,
        nominal_heading_deg=45.0,
        speed_mps=1.5,
        dataset_type="swdd",
        data_dir="data/raw/swdd",
        max_pings=60
    ),
    "northsea_pipeline": MissionConfig(
        mission_id="MSN-NORTHSEA-SUBPIPE-02",
        title="North Sea Pipeline Corridor & Scour Inspection (SubPipe)",
        region="Forties Field Infrastructure Corridor (North Sea)",
        environment="Sandy Ribbons & Shell Hash • Active Subsea Oil & Gas Assets",
        platform="Inspection Class Hydrographic AUV",
        sonar_sensor="Klein Marine 3000 Digital Dual-Beam SSS",
        origin_lat=58.2045,
        origin_lng=1.4512,
        nominal_depth_m=112.0,
        nominal_altitude_m=8.5,
        nominal_heading_deg=315.0,
        speed_mps=1.8,
        dataset_type="subpipe",
        data_dir="data/raw/subpipe",
        max_pings=70
    )
}

class MissionStreamer:
    """
    Real-time continuous AUV mission streamer and hydrographic simulation engine.
    Streams live raw and preprocessed acoustic waterfalls, synchronized bathymetric
    telemetry, and AI contact detections.
    """

    def __init__(self):
        self.orchestrator = PipelineOrchestrator()
        # Default primary mission is the full UMich continuous AUV mission
        self.active_mission_key = "umich_thunderbay"
        self.current_ping_idx = 0
        self.is_playing = False
        self.speed_multiplier = 1.0
        self.custom_missions: Dict[str, MissionConfig] = {}
        self.cached_frames: Dict[str, List[SonarFrameRecord]] = {}
        self._load_all_missions()

    def _load_all_missions(self):
        # 1. Load UMich AI4Shipwrecks Dataset completely
        umich_cfg = PRECONFIGURED_MISSIONS["umich_thunderbay"]
        if os.path.exists(umich_cfg.data_dir):
            patterns = [
                os.path.join(umich_cfg.data_dir, "**", "test", "images", "*.png"),
                os.path.join(umich_cfg.data_dir, "**", "train", "images", "*.png"),
                os.path.join(umich_cfg.data_dir, "**", "extras", "terrain", "images", "*.png"),
                os.path.join(umich_cfg.data_dir, "**", "*.png")
            ]
            all_umich_files = []
            for p in patterns:
                for f in glob.glob(p, recursive=True):
                    if "labels" not in f.lower() and "thumbnail" not in f.lower():
                        all_umich_files.append(f)
            all_umich_files = sorted(list(set(all_umich_files)))

            if all_umich_files:
                enriched = []
                for idx, img_p in enumerate(all_umich_files):
                    heading_rad = np.radians(umich_cfg.nominal_heading_deg)
                    dist_m = idx * umich_cfg.speed_mps * 2.0
                    d_lat = (dist_m * np.cos(heading_rad)) / 111000.0
                    d_lng = (dist_m * np.sin(heading_rad)) / (111000.0 * np.cos(np.radians(umich_cfg.origin_lat)))

                    rec = SonarParser.load_from_file(
                        image_path=img_p,
                        survey_id=umich_cfg.mission_id,
                        ping_index=idx,
                        altitude_m=umich_cfg.nominal_altitude_m + np.sin(idx * 0.15) * 0.7,
                        slant_range_m=50.0,
                        heading_deg=(umich_cfg.nominal_heading_deg + np.sin(idx * 0.1) * 3.0) % 360.0,
                        latitude=umich_cfg.origin_lat + d_lat,
                        longitude=umich_cfg.origin_lng + d_lng
                    )
                    rec.frequency_khz = 410.0
                    enriched.append(rec)

                self.cached_frames["umich_thunderbay"] = enriched
                logger.info(f"Loaded complete UMich AUV continuous mission with {len(enriched)} frames.")

        # 2. Load other preconfigured missions
        for key in ["baltic_debris", "northsea_pipeline"]:
            m_cfg = PRECONFIGURED_MISSIONS[key]
            if os.path.exists(m_cfg.data_dir):
                try:
                    records = list(UnifiedDatasetLoader.stream_dataset_records(
                        m_cfg.dataset_type,
                        m_cfg.data_dir,
                        max_samples=m_cfg.max_pings
                    ))
                    enriched = []
                    for idx, rec in enumerate(records):
                        heading_rad = np.radians(m_cfg.nominal_heading_deg)
                        dist_m = idx * m_cfg.speed_mps * 2.0
                        d_lat = (dist_m * np.cos(heading_rad)) / 111000.0
                        d_lng = (dist_m * np.sin(heading_rad)) / (111000.0 * np.cos(np.radians(m_cfg.origin_lat)))

                        rec.latitude = m_cfg.origin_lat + d_lat
                        rec.longitude = m_cfg.origin_lng + d_lng
                        rec.heading_deg = (m_cfg.nominal_heading_deg + np.sin(idx * 0.2) * 2.0) % 360.0
                        rec.altitude_m = max(5.0, m_cfg.nominal_altitude_m + np.sin(idx * 0.3) * 0.8)
                        rec.survey_id = m_cfg.mission_id
                        rec.ping_index = idx
                        enriched.append(rec)
                    self.cached_frames[key] = enriched
                except Exception as e:
                    logger.error(f"Error loading {key}: {e}")

    def get_available_missions(self) -> List[Dict[str, Any]]:
        all_missions = []
        for key, cfg in {**PRECONFIGURED_MISSIONS, **self.custom_missions}.items():
            num_pings = len(self.cached_frames.get(key, []))
            all_missions.append({
                "key": key,
                "mission_id": cfg.mission_id,
                "title": cfg.title,
                "region": cfg.region,
                "environment": cfg.environment,
                "platform": getattr(cfg, "platform", "Autonomous Underwater Vehicle"),
                "sonar_sensor": getattr(cfg, "sonar_sensor", "Dual-Frequency SSS"),
                "origin_coords": [cfg.origin_lat, cfg.origin_lng],
                "nominal_depth_m": cfg.nominal_depth_m,
                "nominal_altitude_m": cfg.nominal_altitude_m,
                "speed_knots": round(cfg.speed_mps * 1.94384, 1),
                "total_pings": num_pings,
                "is_active": (key == self.active_mission_key)
            })
        return all_missions

    def set_active_mission(self, mission_key: str) -> bool:
        if mission_key in self.cached_frames and len(self.cached_frames[mission_key]) > 0:
            self.active_mission_key = mission_key
            self.current_ping_idx = 0
            return True
        return False

    def seek_ping(self, ping_index: int) -> int:
        frames = self.cached_frames.get(self.active_mission_key, [])
        if not frames:
            return 0
        self.current_ping_idx = max(0, min(ping_index, len(frames) - 1))
        return self.current_ping_idx

    def get_current_frame_payload(self) -> Optional[Dict[str, Any]]:
        frames = self.cached_frames.get(self.active_mission_key, [])
        if not frames or self.current_ping_idx >= len(frames):
            return None

        record = frames[self.current_ping_idx]
        cfg = ({**PRECONFIGURED_MISSIONS, **self.custom_missions}).get(self.active_mission_key)

        # 1. Run AI detection & physical ray-tracing pipeline
        qc_report, contacts = self.orchestrator.process_frame(record, ping_index=self.current_ping_idx)

        # 2. Generate Raw Image Base64
        _, raw_buf = cv2.imencode('.jpg', record.image_array, [cv2.IMWRITE_JPEG_QUALITY, 80])
        raw_b64 = f"data:image/jpeg;base64,{base64.b64encode(raw_buf).decode('utf-8')}"

        # 3. Generate Preprocessed Image (Lee Despeckling + Adaptive CLAHE Enhancement)
        try:
            lee_filtered = SonarFilterEngine.lee_filter(record.image_array, window_size=5, damping_factor=1.0)
            clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
            preprocessed_img = clahe.apply(lee_filtered)
        except Exception:
            preprocessed_img = record.image_array

        _, prep_buf = cv2.imencode('.jpg', preprocessed_img, [cv2.IMWRITE_JPEG_QUALITY, 80])
        prep_b64 = f"data:image/jpeg;base64,{base64.b64encode(prep_buf).decode('utf-8')}"

        # Telemetry
        depth = (cfg.nominal_depth_m if cfg else 35.0) + np.sin(self.current_ping_idx * 0.1) * 0.4
        speed_knots = ((cfg.speed_mps if cfg else 1.5) + np.sin(self.current_ping_idx * 0.4) * 0.05) * 1.94384

        return {
            "event_type": "MISSION_PING",
            "mission_key": self.active_mission_key,
            "mission_id": cfg.mission_id if cfg else "CUSTOM",
            "mission_title": cfg.title if cfg else "Custom Survey",
            "region": cfg.region if cfg else "Survey Zone",
            "platform": getattr(cfg, "platform", "Iver3 AUV"),
            "sonar_sensor": getattr(cfg, "sonar_sensor", "EdgeTech 2205 SSS"),
            "ping_index": self.current_ping_idx,
            "total_pings": len(frames),
            "telemetry": {
                "latitude": round(record.latitude or 0.0, 6),
                "longitude": round(record.longitude or 0.0, 6),
                "heading_deg": round(record.heading_deg or 0.0, 1),
                "altitude_m": round(record.altitude_m or 12.0, 2),
                "depth_m": round(depth, 2),
                "speed_knots": round(speed_knots, 1),
                "frequency_khz": record.frequency_khz,
                "slant_range_m": record.slant_range_m,
                "timestamp": time.time()
            },
            "qc_report": qc_report.to_dict() if hasattr(qc_report, 'to_dict') else qc_report,
            "contacts": contacts,
            "raw_frame_image": raw_b64,
            "preprocessed_frame_image": prep_b64,
            "frame_image": prep_b64,  # Default to enhanced preprocessed view
            "frame_width": record.width,
            "frame_height": record.height
        }

    def advance_ping(self) -> int:
        frames = self.cached_frames.get(self.active_mission_key, [])
        if not frames:
            return 0
        if self.current_ping_idx < len(frames) - 1:
            self.current_ping_idx += 1
        else:
            self.current_ping_idx = 0
        return self.current_ping_idx

    def ingest_zip_survey(self, zip_file_path: str, survey_title: str) -> str:
        extract_dir = os.path.join("data", "uploads", f"survey_{int(time.time())}")
        os.makedirs(extract_dir, exist_ok=True)

        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        patterns = ["**/*.png", "**/*.jpg", "**/*.jpeg", "**/*.tif", "**/*.tiff"]
        image_paths = []
        for p in patterns:
            image_paths.extend(glob.glob(os.path.join(extract_dir, p), recursive=True))

        image_paths = sorted(list(set(image_paths)))
        if not image_paths:
            raise ValueError("No valid sonar image files found in the uploaded ZIP archive.")

        custom_key = f"custom_{int(time.time())}"
        mission_id = f"MSN-UPLOAD-{int(time.time()) % 10000:04d}"

        m_cfg = MissionConfig(
            mission_id=mission_id,
            title=survey_title or f"Custom SSS Survey ({len(image_paths)} Pings)",
            region="Custom Hydrographic Sector",
            environment="Acoustic Sonar Stream • Operator Upload",
            platform="User Ingested Survey System",
            sonar_sensor="Side-Scan Sonar",
            origin_lat=13.0827,
            origin_lng=80.2707,
            nominal_depth_m=35.0,
            nominal_altitude_m=10.0,
            nominal_heading_deg=90.0,
            speed_mps=1.5,
            dataset_type="custom",
            data_dir=extract_dir,
            max_pings=len(image_paths)
        )

        records = []
        for idx, img_p in enumerate(image_paths):
            rec = SonarParser.load_from_file(
                image_path=img_p,
                survey_id=mission_id,
                ping_index=idx,
                altitude_m=10.0,
                slant_range_m=50.0
            )
            dist_m = idx * 3.0
            rec.latitude = m_cfg.origin_lat
            rec.longitude = m_cfg.origin_lng + (dist_m / (111000.0 * np.cos(np.radians(m_cfg.origin_lat))))
            rec.heading_deg = 90.0
            rec.altitude_m = 10.0
            records.append(rec)

        self.custom_missions[custom_key] = m_cfg
        self.cached_frames[custom_key] = records
        self.set_active_mission(custom_key)
        logger.info(f"Successfully ingested custom survey '{mission_id}' with {len(records)} pings.")
        return custom_key

mission_streamer = MissionStreamer()
