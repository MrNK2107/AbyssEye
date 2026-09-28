import os
import glob
import cv2
import json
import numpy as np
from typing import List, Dict, Any, Generator, Optional
from ml.ingestion.sonar_parser import SonarParser, SonarFrameRecord

class UnifiedDatasetLoader:
    """
    Unified Side-Scan Sonar Dataset Loader & Converter for ABYSSEYE.
    Seamlessly discovers and streams raw files from:
      1. SubPipe (SubPipeMini / SubPipeMini2) - Subsea pipelines & telemetry
      2. REMARO SWDD - Sonar Waste and Debris Dataset (mines, walls, obstacles)
      3. UMich AI4Shipwrecks (8623hz41x) - Shipwrecks and seabed anomalies
      4. ABYSSEYE Synthetic & Custom Sonar Surveys
    """

    @staticmethod
    def discover_subpipe_dataset(data_dir: str = "data/raw/subpipe") -> List[str]:
        """Finds all sonar images inside SubPipe directories."""
        patterns = [
            os.path.join(data_dir, "**", "*.png"),
            os.path.join(data_dir, "**", "*.jpg"),
            os.path.join(data_dir, "**", "*.jpeg"),
            os.path.join(data_dir, "**", "*.tif"),
            os.path.join(data_dir, "**", "*.tiff")
        ]
        files = []
        for p in patterns:
            files.extend(glob.glob(p, recursive=True))
        return sorted(list(set(files)))

    @staticmethod
    def discover_swdd_dataset(data_dir: str = "data/raw/swdd") -> List[str]:
        """Finds all images inside REMARO SWDD directory."""
        patterns = [
            os.path.join(data_dir, "**", "*.png"),
            os.path.join(data_dir, "**", "*.jpg"),
            os.path.join(data_dir, "**", "*.tif")
        ]
        files = []
        for p in patterns:
            files.extend(glob.glob(p, recursive=True))
        return sorted(list(set(files)))

    @staticmethod
    def discover_shipwrecks_dataset(data_dir: str = "data/raw/umich_sonar") -> List[str]:
        """Finds all shipwreck sonar images inside AI4Shipwrecks (UMich DeepBlue 8623hz41x)."""
        patterns = [
            os.path.join(data_dir, "**", "*.png"),
            os.path.join(data_dir, "**", "*.jpg"),
            os.path.join(data_dir, "**", "*.tif")
        ]
        files = []
        for p in patterns:
            # Filter out mask/label images if stored alongside or thumbnail
            matched = glob.glob(p, recursive=True)
            for m in matched:
                if "thumbnail" not in m.lower() and "mask" not in m.lower():
                    files.append(m)
        return sorted(list(set(files)))

    @staticmethod
    def get_dataset_summary(raw_dir: str = "data/raw") -> Dict[str, Any]:
        """Returns statistics on all locally discovered datasets."""
        subpipe_imgs = UnifiedDatasetLoader.discover_subpipe_dataset(os.path.join(raw_dir, "subpipe"))
        swdd_imgs = UnifiedDatasetLoader.discover_swdd_dataset(os.path.join(raw_dir, "swdd"))
        shipwreck_imgs = UnifiedDatasetLoader.discover_shipwrecks_dataset(os.path.join(raw_dir, "umich_sonar"))

        return {
            "subpipe": {
                "count": len(subpipe_imgs),
                "path": os.path.join(raw_dir, "subpipe"),
                "sample": subpipe_imgs[:3] if subpipe_imgs else []
            },
            "swdd": {
                "count": len(swdd_imgs),
                "path": os.path.join(raw_dir, "swdd"),
                "sample": swdd_imgs[:3] if swdd_imgs else []
            },
            "ai4shipwrecks": {
                "count": len(shipwreck_imgs),
                "path": os.path.join(raw_dir, "umich_sonar"),
                "sample": shipwreck_imgs[:3] if shipwreck_imgs else []
            },
            "total_real_images": len(subpipe_imgs) + len(swdd_imgs) + len(shipwreck_imgs)
        }

    @staticmethod
    def stream_dataset_records(
        dataset_type: str,
        data_dir: str,
        survey_id: str = "SRV-STREAM",
        max_samples: Optional[int] = None
    ) -> Generator[SonarFrameRecord, None, None]:
        """
        Yields normalized SonarFrameRecords from discovered files.
        """
        dt = dataset_type.lower()
        if "subpipe" in dt:
            file_paths = UnifiedDatasetLoader.discover_subpipe_dataset(data_dir)
            provenance_src = "SubPipe-v1"
        elif "swdd" in dt:
            file_paths = UnifiedDatasetLoader.discover_swdd_dataset(data_dir)
            provenance_src = "REMARO-SWDD"
        elif "shipwreck" in dt or "umich" in dt:
            file_paths = UnifiedDatasetLoader.discover_shipwrecks_dataset(data_dir)
            provenance_src = "UMich-AI4Shipwrecks"
        else:
            file_paths = glob.glob(os.path.join(data_dir, "**", "*.png"), recursive=True)
            provenance_src = "CUSTOM-SSS"

        if max_samples:
            file_paths = file_paths[:max_samples]

        for idx, f_path in enumerate(file_paths):
            try:
                record = SonarParser.load_from_file(
                    image_path=f_path,
                    survey_id=f"{survey_id}-{idx:04d}",
                    ping_index=idx
                )
                record.provenance["source_dataset"] = provenance_src
                record.provenance["file_path"] = f_path
                yield record
            except Exception as e:
                print(f"Warning: Failed to load {f_path}: {e}")
