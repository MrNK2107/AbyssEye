import numpy as np
import cv2
from scipy.ndimage import uniform_filter

class SonarFilterEngine:
    """Preprocesses sonar backscatter images to attenuate speckle while preserving physical shadow edges."""

    @staticmethod
    def normalize_intensity(
        image: np.ndarray,
        lower_percentile: float = 1.0,
        upper_percentile: float = 99.0,
        use_log: bool = True
    ) -> np.ndarray:
        """
        Robust percentile normalization with optional logarithmic dynamic range compression.
        Returns uint8 array in [0, 255].
        """
        img_float = image.astype(np.float32)

        if use_log:
            img_float = np.log1p(img_float)

        p_low = np.percentile(img_float, lower_percentile)
        p_high = np.percentile(img_float, upper_percentile)

        if p_high <= p_low:
            p_high = p_low + 1.0

        normalized = np.clip((img_float - p_low) / (p_high - p_low), 0.0, 1.0)
        return (normalized * 255.0).astype(np.uint8)

    @staticmethod
    def lee_filter(image: np.ndarray, window_size: int = 5, damping_factor: float = 1.0) -> np.ndarray:
        """
        Lee filter for acoustic speckle noise reduction.
        Preserves high-contrast edges (highlights and shadows) while smoothing uniform seabed speckle.
        """
        img_float = image.astype(np.float32)

        # Local mean and local variance
        local_mean = uniform_filter(img_float, size=window_size)
        local_sqr_mean = uniform_filter(img_float**2, size=window_size)
        local_variance = np.maximum(0.0, local_sqr_mean - local_mean**2)

        # Overall noise variance estimation
        overall_variance = np.var(img_float)
        if overall_variance <= 1e-5:
            return image.copy()

        # Weight factor: k = var / (var + noise_var)
        weights = local_variance / (local_variance + overall_variance * damping_factor + 1e-5)
        weights = np.clip(weights, 0.0, 1.0)

        filtered = local_mean + weights * (img_float - local_mean)
        return np.clip(filtered, 0, 255).astype(np.uint8)

    @staticmethod
    def bilateral_filter(image: np.ndarray, d: int = 5, sigma_color: float = 35.0, sigma_space: float = 35.0) -> np.ndarray:
        """Edge-preserving bilateral smoothing."""
        return cv2.bilateralFilter(image, d=d, sigmaColor=sigma_color, sigmaSpace=sigma_space)

    @staticmethod
    def preprocess_pipeline(image: np.ndarray) -> np.ndarray:
        """Standard full preprocessing pipeline."""
        normalized = SonarFilterEngine.normalize_intensity(image)
        filtered = SonarFilterEngine.lee_filter(normalized, window_size=5)
        return filtered
