import numpy as np
import cv2
from skimage.feature import graycomatrix, graycoprops
from dataclasses import dataclass
from typing import Tuple, Dict, Any

@dataclass
class SeabedContextEvidence:
    glcm_contrast_diff: float
    glcm_homogeneity_diff: float
    glcm_energy_diff: float
    glcm_entropy_diff: float
    gradient_var_diff: float
    embedding_cosine_distance: float
    seabed_roughness: float
    isolation_score: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "glcm_contrast_diff": round(self.glcm_contrast_diff, 2),
            "glcm_homogeneity_diff": round(self.glcm_homogeneity_diff, 3),
            "glcm_energy_diff": round(self.glcm_energy_diff, 3),
            "glcm_entropy_diff": round(self.glcm_entropy_diff, 3),
            "gradient_var_diff": round(self.gradient_var_diff, 2),
            "embedding_cosine_distance": round(self.embedding_cosine_distance, 3),
            "seabed_roughness": round(self.seabed_roughness, 2),
            "isolation_score": round(self.isolation_score, 3)
        }


class SeabedContextEngine:
    """
    Multi-Scale Seabed Context Analyzer.
    Compares candidate target texture against immediate surrounding ring and global background
    using 5-metric GLCM texture analysis and neural embedding dissimilarity.
    """

    def __init__(self, glcm_distances=(1, 2), glcm_angles=(0, np.pi/4, np.pi/2, 3*np.pi/4)):
        self.distances = glcm_distances
        self.angles = glcm_angles

    def extract_concentric_crops(
        self,
        full_image: np.ndarray,
        bbox: Tuple[int, int, int, int]
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Extracts concentric crops: Target (1x), Local Ring (2x), Global Background (4x).
        """
        H, W = full_image.shape
        x, y, w, h = bbox
        cx, cy = int(x + w / 2), int(y + h / 2)

        # 1. Target Crop
        target_crop = full_image[max(0, y):min(H, y+h), max(0, x):min(W, x+w)]

        # 2. Local Ring Crop (2W x 2H)
        rw, rh = max(8, w * 2), max(8, h * 2)
        rx0, rx1 = max(0, cx - rw // 2), min(W, cx + rw // 2)
        ry0, ry1 = max(0, cy - rh // 2), min(H, cy + rh // 2)
        ring_crop = full_image[ry0:ry1, rx0:rx1]

        # 3. Global Scene Context (4W x 4H)
        gw, gh = max(16, w * 4), max(16, h * 4)
        gx0, gx1 = max(0, cx - gw // 2), min(W, cx + gw // 2)
        gy0, gy1 = max(0, cy - gh // 2), min(H, cy + gh // 2)
        global_crop = full_image[gy0:gy1, gx0:gx1]

        return target_crop, ring_crop, global_crop

    def _compute_glcm_features(self, crop: np.ndarray) -> Dict[str, float]:
        if crop is None or crop.size < 16:
            return {"contrast": 0.0, "homogeneity": 1.0, "energy": 1.0, "entropy": 0.0, "grad_var": 0.0}

        # Quantize to 16 gray levels for fast robust GLCM
        quantized = (crop.astype(np.float32) / 16.0).astype(np.uint8)
        glcm = graycomatrix(quantized, distances=self.distances, angles=self.angles, levels=16, symmetric=True, normed=True)

        contrast = float(np.mean(graycoprops(glcm, 'contrast')))
        homogeneity = float(np.mean(graycoprops(glcm, 'homogeneity')))
        energy = float(np.mean(graycoprops(glcm, 'energy')))

        # Entropy calculation
        glcm_nz = glcm[glcm > 0]
        entropy = float(-np.sum(glcm_nz * np.log2(glcm_nz)))

        # Gradient variance
        sobel_x = cv2.Sobel(crop.astype(np.float32), cv2.CV_32F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(crop.astype(np.float32), cv2.CV_32F, 0, 1, ksize=3)
        grad_mag = np.sqrt(sobel_x**2 + sobel_y**2)
        grad_var = float(np.var(grad_mag))

        return {
            "contrast": contrast,
            "homogeneity": homogeneity,
            "energy": energy,
            "entropy": entropy,
            "grad_var": grad_var
        }

    def analyze_context(
        self,
        full_image: np.ndarray,
        bbox: Tuple[int, int, int, int]
    ) -> SeabedContextEvidence:
        target, ring, global_scene = self.extract_concentric_crops(full_image, bbox)

        feat_target = self._compute_glcm_features(target)
        feat_ring = self._compute_glcm_features(ring)

        # Texture feature deltas
        d_contrast = abs(feat_target["contrast"] - feat_ring["contrast"])
        d_homogeneity = abs(feat_target["homogeneity"] - feat_ring["homogeneity"])
        d_energy = abs(feat_target["energy"] - feat_ring["energy"])
        d_entropy = abs(feat_target["entropy"] - feat_ring["entropy"])
        d_grad_var = abs(feat_target["grad_var"] - feat_ring["grad_var"])

        # Simple normalized histogram cosine distance as lightweight embedding distance
        hist_t, _ = np.histogram(target, bins=16, range=(0, 256), density=True)
        hist_r, _ = np.histogram(ring, bins=16, range=(0, 256), density=True)
        cos_sim = np.dot(hist_t, hist_r) / (np.linalg.norm(hist_t) * np.linalg.norm(hist_r) + 1e-6)
        embedding_dist = float(np.clip(1.0 - cos_sim, 0.0, 2.0))

        # Seafloor roughness (background intensity standard deviation)
        roughness = float(np.std(global_scene)) if global_scene.size > 0 else 20.0

        # Isolation score: high contrast difference relative to background roughness
        isolation = float(np.clip((d_contrast / max(1.0, roughness)) * 2.0 + embedding_dist, 0.0, 1.0))

        return SeabedContextEvidence(
            glcm_contrast_diff=d_contrast,
            glcm_homogeneity_diff=d_homogeneity,
            glcm_energy_diff=d_energy,
            glcm_entropy_diff=d_entropy,
            gradient_var_diff=d_grad_var,
            embedding_cosine_distance=embedding_dist,
            seabed_roughness=roughness,
            isolation_score=isolation
        )
