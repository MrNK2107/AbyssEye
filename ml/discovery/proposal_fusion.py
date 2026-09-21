import numpy as np
from typing import List, Tuple
from ml.discovery.classical_proposal import CandidateProposal

class ProposalFusionEngine:
    """
    Fuses candidate contact proposals from multiple discovery engines:
    Classical CV + PatchCore Anomaly + Supervised Detector.
    Merges overlapping proposals via IoU clustering while retaining multi-source provenance.
    """

    @staticmethod
    def calculate_iou(boxA: Tuple[int, int, int, int], boxB: Tuple[int, int, int, int]) -> float:
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[0] + boxA[2], boxB[0] + boxB[2])
        yB = min(boxA[1] + boxA[3], boxB[1] + boxB[3])

        interW = max(0, xB - xA)
        interH = max(0, yB - yA)
        interArea = interW * interH

        boxAArea = boxA[2] * boxA[3]
        boxBArea = boxB[2] * boxB[3]
        unionArea = boxAArea + boxBArea - interArea

        if unionArea <= 0:
            return 0.0
        return float(interArea / unionArea)

    @classmethod
    def fuse_proposals(
        cls,
        proposals: List[CandidateProposal],
        iou_threshold: float = 0.30
    ) -> List[CandidateProposal]:
        if not proposals:
            return []

        # Sort by confidence descending
        sorted_props = sorted(proposals, key=lambda p: p.confidence, reverse=True)
        fused: List[CandidateProposal] = []
        visited = [False] * len(sorted_props)

        for i in range(len(sorted_props)):
            if visited[i]:
                continue

            current = sorted_props[i]
            cluster = [current]
            visited[i] = True

            for j in range(i + 1, len(sorted_props)):
                if visited[j]:
                    continue
                other = sorted_props[j]
                if cls.calculate_iou(current.bbox, other.bbox) >= iou_threshold:
                    cluster.append(other)
                    visited[j] = True

            # Merge cluster into single representative candidate
            all_sources = list(set([src for p in cluster for src in p.sources]))
            max_conf = max(p.confidence for p in cluster)
            max_anomaly = max(p.anomaly_score for p in cluster)
            max_peak = max(p.peak_intensity for p in cluster)
            mean_int = float(np.mean([p.mean_intensity for p in cluster]))

            # Determine bounding box union
            min_x = min(p.bbox[0] for p in cluster)
            min_y = min(p.bbox[1] for p in cluster)
            max_x = max(p.bbox[0] + p.bbox[2] for p in cluster)
            max_y = max(p.bbox[1] + p.bbox[3] for p in cluster)
            union_bbox = (min_x, min_y, max_x - min_x, max_y - min_y)
            cx = float(min_x + (max_x - min_x) / 2.0)
            cy = float(min_y + (max_y - min_y) / 2.0)

            # Check if any detector class exists
            det_class = "unknown"
            det_conf = 0.0
            for p in cluster:
                if p.detector_class != "unknown" and p.detector_conf > det_conf:
                    det_class = p.detector_class
                    det_conf = p.detector_conf

            merged_id = f"CONT-PROPOSAL-{len(fused)+1:04d}"
            fused.append(CandidateProposal(
                proposal_id=merged_id,
                bbox=union_bbox,
                centroid=(cx, cy),
                confidence=max_conf,
                sources=all_sources,
                area_px=union_bbox[2] * union_bbox[3],
                mean_intensity=mean_int,
                peak_intensity=max_peak,
                aspect_ratio=float(max(union_bbox[2], union_bbox[3]) / max(1, min(union_bbox[2], union_bbox[3]))),
                detector_class=det_class,
                detector_conf=det_conf,
                anomaly_score=max_anomaly
            ))

        return fused
