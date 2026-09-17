import os
import glob
import cv2
import json
import numpy as np
from typing import List, Dict, Any, Generator, Optional
from ml.ingestion.sonar_parser import SonarParser, SonarFrameRecord

class UnifiedDatasetLoader:
    """
    Unified Side-Scan Sonar Dataset Loader & Converter.
    Seamlessly discovers and streams raw files from SubPipe (SubPipeMini / Mini2),
    REMARO SWDD, UMich Sonar, BenthicNet, and local synthetic directories.
    """

    @staticmethod
    def discover_subpipe_dataset(data_dir: str = "data/raw/subpipe") -> List[str]:
        """Finds all images inside SubPipe directory."""
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
    def stream_dataset_records(
        dataset_type: str,
        data_dir: str,
        survey_id: str = "SRV-STREAM"
    ) -> Generator[SonarFrameRecord, None, None]:
        """
        Yields normalized SonarFrameRecords from discovered files.
        """
        if dataset_type.lower() == "subpipe":
            file_paths = UnifiedDatasetLoader.discover_subpipe_dataset(data_dir)
            provenance_src = "SubPipe-v1"
        elif dataset_type.lower() == "swdd":
            file_paths = UnifiedDatasetLoader.discover_swdd_dataset(data_dir)
            provenance_src = "REMARO-SWDD"
        else:
            file_paths = glob.glob(os.path.join(data_dir, "**", "*.png"), recursive=True)
            provenance_src = "CUSTOM-SSS"

        for idx, f_path in enumerate(file_paths):
            try:
                record = SonarParser.load_from_file(
                    image_path=f_path,
                    survey_id=survey_id,
                    ping_index=idx
                )
                record.provenance["source_dataset"] = provenance_src
                yield record
            except Exception as e:
                print(f"Warning: Failed to load {f_path}: {e}")
