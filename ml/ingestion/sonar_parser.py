from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Tuple
import os
import json
import numpy as np
import cv2

@dataclass
class SonarFrameRecord:
    """Standardized internal representation of a Side-Scan Sonar frame/ping."""
    frame_id: str
    survey_id: str
    ping_index: int
    image_array: np.ndarray  # 2D array uint8 [0, 255] or float32 [0.0, 1.0]
    slant_range_m: float = 50.0
    altitude_m: Optional[float] = 10.0
    heading_deg: Optional[float] = 0.0
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    frequency_khz: float = 900.0
    channel: str = "DUAL"  # 'PORT', 'STARBOARD', 'DUAL'
    pixel_resolution_m: float = 0.05
    provenance: Dict[str, Any] = field(default_factory=dict)

    @property
    def height(self) -> int:
        return self.image_array.shape[0]

    @property
    def width(self) -> int:
        return self.image_array.shape[1]


class SonarParser:
    """Parses raw sonar images, GeoTIFFs, waterfalls, and sidecar JSON metadata."""

    @staticmethod
    def load_from_file(
        image_path: str,
        sidecar_meta_path: Optional[str] = None,
        survey_id: str = "SURVEY-DEFAULT",
        ping_index: int = 0,
        altitude_m: Optional[float] = None,
        slant_range_m: Optional[float] = None,
        heading_deg: Optional[float] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ) -> SonarFrameRecord:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Sonar image file not found: {image_path}")

        # Load image in grayscale
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise ValueError(f"Failed to decode sonar image from {image_path}")

        # Default metadata
        metadata: Dict[str, Any] = {
            "slant_range_m": 50.0,
            "altitude_m": 10.0,
            "heading_deg": 0.0,
            "latitude": None,
            "longitude": None,
            "frequency_khz": 900.0,
            "channel": "DUAL",
            "pixel_resolution_m": 0.05,
            "real": True,
            "synthetic": False,
            "source_dataset": "UNKNOWN"
        }

        # Check for sidecar JSON
        if sidecar_meta_path is None:
            base_json = os.path.splitext(image_path)[0] + ".json"
            if os.path.exists(base_json):
                sidecar_meta_path = base_json

        if sidecar_meta_path and os.path.exists(sidecar_meta_path):
            try:
                with open(sidecar_meta_path, 'r') as f:
                    meta_json = json.load(f)
                    metadata.update(meta_json)
            except Exception as e:
                print(f"Warning: Failed to parse sidecar JSON {sidecar_meta_path}: {e}")

        frame_id = os.path.splitext(os.path.basename(image_path))[0]

        return SonarFrameRecord(
            frame_id=frame_id,
            survey_id=survey_id,
            ping_index=ping_index,
            image_array=img,
            slant_range_m=slant_range_m if slant_range_m is not None else float(metadata.get("slant_range_m", 50.0)),
            altitude_m=altitude_m if altitude_m is not None else (float(metadata["altitude_m"]) if metadata.get("altitude_m") is not None else None),
            heading_deg=heading_deg if heading_deg is not None else (float(metadata["heading_deg"]) if metadata.get("heading_deg") is not None else None),
            latitude=latitude if latitude is not None else (float(metadata["latitude"]) if metadata.get("latitude") is not None else None),
            longitude=longitude if longitude is not None else (float(metadata["longitude"]) if metadata.get("longitude") is not None else None),
            frequency_khz=float(metadata.get("frequency_khz", 900.0)),
            channel=str(metadata.get("channel", "DUAL")).upper(),
            pixel_resolution_m=float(metadata.get("pixel_resolution_m", 0.05)),
            provenance={
                "real": metadata.get("real", True),
                "synthetic": metadata.get("synthetic", False),
                "source_dataset": metadata.get("source_dataset", "UNKNOWN"),
                "file_path": image_path
            }
        )
