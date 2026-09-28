#!/usr/bin/env python3
"""
ABYSSEYE Batch Dataset Processing CLI
Run high-throughput multi-core feature extraction and contact detection
across extracted raw datasets.
"""

import os
import sys
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ml.ingestion.parallel_batch_extractor import ParallelBatchExtractor

def main():
    parser = argparse.ArgumentParser(description="AbyssEye High-Throughput Parallel Batch Sonar Processor")
    parser.add_argument("--dataset", type=str, choices=["subpipe", "swdd", "shipwreck", "all"], default="subpipe", help="Dataset type to process")
    parser.add_argument("--path", type=str, default=None, help="Custom dataset root path")
    parser.add_argument("--max-samples", type=int, default=50, help="Maximum number of frames to process")
    parser.add_argument("--workers", type=int, default=None, help="Number of parallel worker processes")
    parser.add_argument("--output", type=str, default="experiments/results/batch_extraction_results.json", help="Output JSON results path")

    args = parser.parse_args()

    extractor = ParallelBatchExtractor(max_workers=args.workers)

    configs = {
        "subpipe": ("subpipe", args.path or "data/raw/subpipe"),
        "swdd": ("swdd", args.path or "data/raw/swdd"),
        "shipwreck": ("shipwreck", args.path or "data/raw/umich_sonar")
    }

    if args.dataset == "all":
        for ds_name, (ds_type, ds_path) in configs.items():
            if os.path.exists(ds_path):
                out = f"experiments/results/batch_{ds_name}.json"
                extractor.process_dataset(ds_type, ds_path, max_samples=args.max_samples, output_file=out)
    else:
        ds_type, ds_path = configs[args.dataset]
        if not os.path.exists(ds_path):
            print(f"Error: Dataset path {ds_path} does not exist.")
            sys.exit(1)
        extractor.process_dataset(ds_type, ds_path, max_samples=args.max_samples, output_file=args.output)

if __name__ == "__main__":
    main()
