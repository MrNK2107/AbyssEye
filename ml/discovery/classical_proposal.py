import numpy as np
import cv2
from dataclasses import dataclass
from typing import List, Tuple, Dict, Any

@dataclass
class CandidateProposal:
    proposal_id: str
    bbox: Tuple[int, int, int, int]  # (x, y, w, h)
    centroid: Tuple[float, float]     # (cx, cy)
    confidence: float
    sources: List[str]               # e.g. ['classical_cv', 'patchcore']
    area_px: int
    mean_intensity: float
    peak_intensity: float
    aspect_ratio: float
    detector_class: str = "unknown"
    detector_conf: float = 0.0
    anomaly_score: float = 0.0


class ClassicalProposalEngine:
    """
    High-recall adaptive background proposal generator for side-scan sonar.
    Discovers acoustic highlight anomalies against non-uniform seafloor backscatter.
    """

    def __init__(
        self,
        local_window_size: int = 64,
        k_sigma: float = 1.8,
        min_area_px: int = 15,
        max_area_px: int = 3500,
        morph_kernel_size: int = 3
    ):
        self.local_window_size = local_window_size
        self.k_sigma = k_sigma
        self.min_area_px = min_area_px
        self.max_area_px = max_area_px
        self.morph_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (morph_kernel_size, morph_kernel_size))

    def detect_proposals(self, image: np.ndarray, frame_id: str = "frame") -> List[CandidateProposal]:
        if image is None or image.size == 0:
            return []

        img_float = image.astype(np.float32)
        H, W = image.shape

        # 1. Local background mean and standard deviation
        local_mean = cv2.blur(img_float, (self.local_window_size, self.local_window_size))
        local_sqr = cv2.blur(img_float**2, (self.local_window_size, self.local_window_size))
        local_std = np.sqrt(np.maximum(1.0, local_sqr - local_mean**2))

        # 2. Adaptive thresholding for bright acoustic returns
        threshold_map = local_mean + self.k_sigma * local_std
        binary_mask = (img_float > threshold_map).astype(np.uint8) * 255

        # 3. Morphological close-open to clean speckle
        closed_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, self.morph_kernel)
        opened_mask = cv2.morphologyEx(closed_mask, cv2.MORPH_OPEN, self.morph_kernel)

        # 4. Connected components analysis
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(opened_mask, connectivity=8)

        proposals = []
        for i in range(1, num_labels):
            area = int(stats[i, cv2.CC_STAT_AREA])
            if self.min_area_px <= area <= self.max_area_px:
                x = int(stats[i, cv2.CC_STAT_LEFT])
                y = int(stats[i, cv2.CC_STAT_TOP])
                w = int(stats[i, cv2.CC_STAT_WIDTH])
                h = int(stats[i, cv2.CC_STAT_HEIGHT])
                cx, cy = float(centroids[i][0]), float(centroids[i][1])

                crop = image[y:y+h, x:x+w]
                mean_val = float(np.mean(crop)) if crop.size > 0 else 0.0
                peak_val = float(np.max(crop)) if crop.size > 0 else 0.0
                aspect_ratio = float(max(w, h) / max(1, min(w, h)))

                # Normalized confidence based on peak local z-score
                local_z = (peak_val - local_mean[int(cy), int(cx)]) / max(1.0, local_std[int(cy), int(cx)])
                conf = float(np.clip(local_z / 4.0, 0.2, 0.98))

                prop_id = f"PROP-CLASSICAL-{frame_id}-{len(proposals)+1:03d}"
                proposals.append(CandidateProposal(
                    proposal_id=prop_id,
                    bbox=(x, y, w, h),
                    centroid=(cx, cy),
                    confidence=conf,
                    sources=["classical_cv"],
                    area_px=area,
                    mean_intensity=mean_val,
                    peak_intensity=peak_val,
                    aspect_ratio=aspect_ratio
                ))

        return proposals
