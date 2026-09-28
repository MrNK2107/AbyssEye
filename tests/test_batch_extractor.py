import os
import pytest
from ml.ingestion.parallel_batch_extractor import ParallelBatchExtractor

def test_parallel_batch_extractor():
    extractor = ParallelBatchExtractor(max_workers=2)
    
    # Run on synthetic or small subset
    if os.path.exists("data/raw/subpipe"):
        summary = extractor.process_dataset("subpipe", "data/raw/subpipe", max_samples=4)
        assert summary["total_frames_processed"] == 4
        assert summary["throughput_fps"] > 0
        assert summary["workers_used"] == 2
