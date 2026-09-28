"""
ABYSSEYE: High-Throughput Parallel Batch Sonar Processing Engine
Enables industrial-scale batch extraction, inference, and feature caching across
tens of thousands of raw sonar frames using multiprocessing worker pools.
"""

import os
import sys
import time
import json
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
import numpy as np

# Add project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from ml.ingestion.dataset_loader import UnifiedDatasetLoader
from ml.fusion.feature_vector import FeatureVectorAssembler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ParallelBatchExtractor")

def _process_single_frame_worker(record: Any, ping_idx: int) -> Dict[str, Any]:
    """
    Worker process target: initializes an isolated PipelineOrchestrator instance
    and processes a single frame without sharing memory or locks.
    """
    from backend.app.services.pipeline_orchestrator import PipelineOrchestrator
    frame_id = getattr(record, "frame_id", None) or (record.get("frame_id") if isinstance(record, dict) else f"ping_{ping_idx}")
    dataset_type = getattr(record, "dataset_type", None) or (record.get("dataset_type") if isinstance(record, dict) else "unknown")

    try:
        orchestrator = PipelineOrchestrator()
        qc_report, contacts = orchestrator.process_frame(record, ping_index=ping_idx)
        
        extracted_features = []
        for c in contacts:
            f_dict = c.get("feature_vector", {})
            f_vec = FeatureVectorAssembler.to_numpy_array(f_dict).tolist()
            extracted_features.append({
                "contact_id": c.get("contact_id"),
                "classification": c.get("classification"),
                "confidence": c.get("confidence"),
                "features": f_vec,
                "evidence": c.get("evidence_graph")
            })
            
        return {
            "status": "SUCCESS",
            "frame_id": frame_id,
            "dataset_type": dataset_type,
            "qc_passed": qc_report.get("overall_pass", False),
            "snr_db": qc_report.get("snr_db", 0.0),
            "num_contacts": len(contacts),
            "contacts": extracted_features
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "frame_id": frame_id,
            "dataset_type": dataset_type,
            "error": str(e)
        }

class ParallelBatchExtractor:
    """
    Industrial batch extraction manager supporting parallel multi-core execution,
    checkpointing, and streaming export to JSON/Parquet.
    """
    def __init__(self, max_workers: Optional[int] = None):
        self.max_workers = max_workers or min(os.cpu_count() or 4, 8)

    def process_dataset(
        self,
        dataset_type: str,
        root_dir: str,
        max_samples: int = 100,
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        start_time = time.time()
        logger.info(f"Starting batch extraction on {dataset_type} ({root_dir}) with {self.max_workers} workers (Limit: {max_samples})...")
        
        records = list(UnifiedDatasetLoader.stream_dataset_records(dataset_type, root_dir, max_samples=max_samples))
        total_records = len(records)
        logger.info(f"Discovered {total_records} sonar frames for processing.")
        
        results = []
        total_contacts_found = 0
        
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_idx = {
                executor.submit(_process_single_frame_worker, rec, idx): idx 
                for idx, rec in enumerate(records)
            }
            
            for future in as_completed(future_to_idx):
                res = future.result()
                results.append(res)
                if res.get("status") == "SUCCESS":
                    total_contacts_found += res.get("num_contacts", 0)

        elapsed = time.time() - start_time
        fps = total_records / max(elapsed, 0.001)
        
        summary = {
            "dataset_type": dataset_type,
            "total_frames_processed": total_records,
            "total_contacts_extracted": total_contacts_found,
            "elapsed_seconds": round(elapsed, 2),
            "throughput_fps": round(fps, 2),
            "workers_used": self.max_workers
        }
        
        if output_file:
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
            with open(output_file, "w") as f:
                json.dump({"summary": summary, "records": results}, f, indent=2)
            logger.info(f"Saved batch results to {output_file}")
            
        logger.info(f"Batch completed: {total_records} frames, {total_contacts_found} contacts in {elapsed:.2f}s ({fps:.2f} fps)")
        return summary
