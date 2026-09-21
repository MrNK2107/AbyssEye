import numpy as np
import cv2
import torch
import torch.nn as nn
from typing import List, Tuple, Optional
from ml.discovery.classical_proposal import CandidateProposal

class PatchCoreAnomalyDetector:
    """
    PatchCore Feature-Memory Anomaly Discovery Engine for Sonar.
    Discovers open-set acoustic anomalies (such as ghost nets) without requiring positive debris labels.
    """

    def __init__(
        self,
        coreset_sampling_ratio: float = 0.1,
        patch_size: int = 16,
        stride: int = 8,
        anomaly_threshold: float = 0.60
    ):
        self.coreset_sampling_ratio = coreset_sampling_ratio
        self.patch_size = patch_size
        self.stride = stride
        self.anomaly_threshold = anomaly_threshold
        self.memory_bank: Optional[np.ndarray] = None
        self.feature_dim: int = 64

    def extract_patch_features(self, image: np.ndarray) -> Tuple[np.ndarray, List[Tuple[int, int]]]:
        """
        Extracts multi-scale texture descriptor vectors for overlapping spatial patches.
        """
        H, W = image.shape
        img_float = image.astype(np.float32) / 255.0

        features = []
        positions = []

        # Extract multi-channel Gabor & gradient spatial features
        sobel_x = cv2.Sobel(img_float, cv2.CV_32F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(img_float, cv2.CV_32F, 0, 1, ksize=3)
        grad_mag = np.sqrt(sobel_x**2 + sobel_y**2)

        for y in range(0, H - self.patch_size + 1, self.stride):
            for x in range(0, W - self.patch_size + 1, self.stride):
                p_int = img_float[y:y+self.patch_size, x:x+self.patch_size]
                p_grad = grad_mag[y:y+self.patch_size, x:x+self.patch_size]

                # Statistical descriptor (mean, std, percentiles, gradients)
                hist_int, _ = np.histogram(p_int, bins=16, range=(0.0, 1.0))
                hist_grad, _ = np.histogram(p_grad, bins=16, range=(0.0, 1.0))
                stats = np.array([
                    np.mean(p_int), np.std(p_int), np.max(p_int), np.min(p_int),
                    np.mean(p_grad), np.std(p_grad), np.max(p_grad)
                ], dtype=np.float32)

                feat_vec = np.concatenate([hist_int / 16.0, hist_grad / 16.0, stats])
                # Normalize feature vector
                norm = np.linalg.norm(feat_vec) + 1e-6
                features.append(feat_vec / norm)
                positions.append((x + self.patch_size // 2, y + self.patch_size // 2))

        if len(features) == 0:
            return np.zeros((0, 39), dtype=np.float32), []

        return np.array(features, dtype=np.float32), positions

    def fit_normal_seabed(self, normal_images: List[np.ndarray]):
        """
        Builds the reference seafloor memory bank from normal seabed background sonar images.
        Applies greedy coreset subsampling.
        """
        all_features = []
        for img in normal_images:
            feats, _ = self.extract_patch_features(img)
            if len(feats) > 0:
                all_features.append(feats)

        if len(all_features) == 0:
            self.memory_bank = np.random.randn(100, 39).astype(np.float32)
            return

        full_bank = np.vstack(all_features)
        total_samples = len(full_bank)
        num_coreset = max(10, int(total_samples * self.coreset_sampling_ratio))

        # Greedy k-center coreset subsampling
        if total_samples <= num_coreset:
            self.memory_bank = full_bank
        else:
            selected_indices = [np.random.randint(0, total_samples)]
            min_dists = np.linalg.norm(full_bank - full_bank[selected_indices[0]], axis=1)

            for _ in range(1, num_coreset):
                farthest_idx = int(np.argmax(min_dists))
                selected_indices.append(farthest_idx)
                new_dists = np.linalg.norm(full_bank - full_bank[farthest_idx], axis=1)
                min_dists = np.minimum(min_dists, new_dists)

            self.memory_bank = full_bank[selected_indices]

    def compute_anomaly_map(self, image: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Computes the dense spatial anomaly heatmap A(x, y) in [0, 1].
        """
        H, W = image.shape
        if self.memory_bank is None or len(self.memory_bank) == 0:
            # Initialize default baseline memory bank if unfitted
            self.fit_normal_seabed([np.random.uniform(70, 140, (H, W)).astype(np.uint8)])

        feats, positions = self.extract_patch_features(image)
        if len(feats) == 0:
            return np.zeros((H, W), dtype=np.float32), 0.0

        # Compute nearest neighbor Euclidean distances to memory bank
        # ||z - m||_2
        diffs = feats[:, np.newaxis, :] - self.memory_bank[np.newaxis, :, :]
        dists = np.sqrt(np.sum(diffs**2, axis=-1))
        min_dists = np.min(dists, axis=1)  # (N_patches,)

        # Build 2D heatmap
        anomaly_map = np.zeros((H, W), dtype=np.float32)
        count_map = np.zeros((H, W), dtype=np.float32)
        half_p = self.patch_size // 2

        for (cx, cy), dist in zip(positions, min_dists):
            y0 = max(0, cy - half_p)
            y1 = min(H, cy + half_p)
            x0 = max(0, cx - half_p)
            x1 = min(W, cx + half_p)
            anomaly_map[y0:y1, x0:x1] += dist
            count_map[y0:y1, x0:x1] += 1.0

        count_map = np.maximum(1.0, count_map)
        anomaly_map = anomaly_map / count_map

        # Gaussian smoothing
        smoothed = cv2.GaussianBlur(anomaly_map, (15, 15), 3.0)

        # Normalize to [0, 1] range based on empirical anomaly scaling
        norm_map = np.clip((smoothed - 0.15) / 0.70, 0.0, 1.0)
        peak_score = float(np.max(norm_map))

        return norm_map, peak_score

    def detect_proposals(self, image: np.ndarray, frame_id: str = "frame") -> List[CandidateProposal]:
        """Surfaces candidate anomalous regions exceeding anomaly threshold."""
        anomaly_map, peak_score = self.compute_anomaly_map(image)
        binary_mask = (anomaly_map > self.anomaly_threshold).astype(np.uint8) * 255

        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary_mask, connectivity=8)

        proposals = []
        for i in range(1, num_labels):
            area = int(stats[i, cv2.CC_STAT_AREA])
            if area >= 20:
                x = int(stats[i, cv2.CC_STAT_LEFT])
                y = int(stats[i, cv2.CC_STAT_TOP])
                w = int(stats[i, cv2.CC_STAT_WIDTH])
                h = int(stats[i, cv2.CC_STAT_HEIGHT])
                cx, cy = float(centroids[i][0]), float(centroids[i][1])

                crop_anomaly = anomaly_map[y:y+h, x:x+w]
                score = float(np.max(crop_anomaly)) if crop_anomaly.size > 0 else 0.0

                crop_img = image[y:y+h, x:x+w]
                mean_int = float(np.mean(crop_img)) if crop_img.size > 0 else 0.0
                peak_int = float(np.max(crop_img)) if crop_img.size > 0 else 0.0
                aspect_ratio = float(max(w, h) / max(1, min(w, h)))

                prop_id = f"PROP-PATCHCORE-{frame_id}-{len(proposals)+1:03d}"
                proposals.append(CandidateProposal(
                    proposal_id=prop_id,
                    bbox=(x, y, w, h),
                    centroid=(cx, cy),
                    confidence=score,
                    sources=["patchcore_anomaly"],
                    area_px=area,
                    mean_intensity=mean_int,
                    peak_intensity=peak_int,
                    aspect_ratio=aspect_ratio,
                    anomaly_score=score
                ))

        return proposals
