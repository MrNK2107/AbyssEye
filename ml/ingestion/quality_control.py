from dataclasses import dataclass
from typing import Dict, Any, Tuple
import numpy as np

@dataclass
class QCReport:
    status: str  # 'EXCELLENT', 'DEGRADED', 'CORRUPTED'
    snr_db: float
    saturation_pct: float
    mean_intensity: float
    std_intensity: float
    bottom_lock_valid: bool
    issues: list

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "snr_db": round(self.snr_db, 2),
            "saturation_pct": round(self.saturation_pct, 2),
            "mean_intensity": round(self.mean_intensity, 2),
            "std_intensity": round(self.std_intensity, 2),
            "bottom_lock_valid": self.bottom_lock_valid,
            "issues": self.issues
        }


class QualityControlEngine:
    """Automated sensor QC inspection for side-scan sonar imagery."""

    def __init__(
        self,
        max_saturation_pct: float = 5.0,
        min_snr_db: float = 8.0,
        min_altitude_m: float = 1.5
    ):
        self.max_saturation_pct = max_saturation_pct
        self.min_snr_db = min_snr_db
        self.min_altitude_m = min_altitude_m

    def evaluate(self, image: np.ndarray, altitude_m: float = None) -> QCReport:
        if image is None or image.size == 0:
            return QCReport(
                status="CORRUPTED",
                snr_db=0.0,
                saturation_pct=100.0,
                mean_intensity=0.0,
                std_intensity=0.0,
                bottom_lock_valid=False,
                issues=["Empty or unreadable image array"]
            )

        img_float = image.astype(np.float32)
        total_pixels = img_float.size

        # 1. Saturation check (intensity >= 254)
        saturated_pixels = np.sum(img_float >= 254.0)
        saturation_pct = (saturated_pixels / total_pixels) * 100.0

        # 2. Intensity statistics
        mean_int = float(np.mean(img_float))
        std_int = float(np.std(img_float))

        # 3. SNR estimation: estimate signal power over lower 10th percentile noise floor
        noise_floor = float(np.percentile(img_float, 10))
        signal_power = float(np.percentile(img_float, 90))

        if noise_floor <= 0.01:
            noise_floor = 0.01

        snr_linear = max(0.1, signal_power / noise_floor)
        snr_db = 10.0 * np.log10(snr_linear)

        # 4. Bottom-lock check
        bottom_lock_valid = True
        issues = []

        if altitude_m is not None:
            if altitude_m < self.min_altitude_m:
                bottom_lock_valid = False
                issues.append(f"Towfish altitude ({altitude_m:.1f}m) below safe bottom-lock threshold ({self.min_altitude_m}m)")
        else:
            issues.append("Altitude metadata unavailable")

        if saturation_pct > self.max_saturation_pct:
            issues.append(f"High saturation clipping: {saturation_pct:.1f}% >= {self.max_saturation_pct}%")

        if snr_db < self.min_snr_db:
            issues.append(f"Low acoustic SNR: {snr_db:.1f} dB < {self.min_snr_db} dB")

        # 5. Final Status Decision
        if saturation_pct > 25.0 or snr_db < 3.0 or std_int < 2.0:
            status = "CORRUPTED"
        elif len(issues) > 0:
            status = "DEGRADED"
        else:
            status = "EXCELLENT"

        return QCReport(
            status=status,
            snr_db=snr_db,
            saturation_pct=saturation_pct,
            mean_intensity=mean_int,
            std_intensity=std_int,
            bottom_lock_valid=bottom_lock_valid,
            issues=issues
        )
