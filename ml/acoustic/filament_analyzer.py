import numpy as np
import cv2
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class FilamentEvidence:
    filament_density: float
    mesh_periodicity_index: float
    boundary_tortuosity: float
    is_net_like: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "filament_density": round(self.filament_density, 3),
            "mesh_periodicity_index": round(self.mesh_periodicity_index, 3),
            "boundary_tortuosity": round(self.boundary_tortuosity, 3),
            "is_net_like": self.is_net_like
        }


class GhostNetFilamentAnalyzer:
    """
    Novelty Signature Extractor for Ghost Fishing Nets & Entangled Gear.
    Analyzes multi-orientation filament striations, mesh periodicity, and boundary tortuosity.
    """

    def __init__(self, orientations=(0, 45, 90, 135), wavelengths=(3, 5, 8)):
        self.orientations = orientations
        self.wavelengths = wavelengths
        self.filters = self._build_gabor_bank()

    def _build_gabor_bank(self):
        filters = []
        for theta_deg in self.orientations:
            theta = np.radians(theta_deg)
            for lam in self.wavelengths:
                kernel = cv2.getGaborKernel(
                    ksize=(11, 11),
                    sigma=2.5,
                    theta=theta,
                    lambd=lam,
                    gamma=0.5,
                    psi=0,
                    ktype=cv2.CV_32F
                )
                # Ensure zero-mean Gabor filter to eliminate DC bias
                kernel = kernel - np.mean(kernel)
                filters.append(kernel)
        return filters

    def analyze_patch(self, patch: np.ndarray) -> FilamentEvidence:
        if patch is None or patch.size < 64:
            return FilamentEvidence(0.0, 0.0, 1.0, False)

        p_raw = patch.astype(np.float32) / 255.0
        # Zero-center patch to isolate texture and filaments from background illumination
        p_float = p_raw - np.mean(p_raw)

        # 1. Multi-orientation Gabor Energy
        energies = []
        for kern in self.filters:
            filtered = cv2.filter2D(p_float, cv2.CV_32F, kern)
            energies.append(np.mean(np.abs(filtered)))

        filament_density = float(np.mean(energies) * 10.0)
        filament_density = float(np.clip(filament_density, 0.0, 1.0))

        # 2. Mesh Periodicity via 2D FFT Power Spectrum
        dft = np.fft.fft2(p_float)
        dft_shift = np.fft.fftshift(dft)
        mag_spec = np.abs(dft_shift)

        H, W = mag_spec.shape
        cy, cx = H // 2, W // 2
        r_inner = max(2, min(H, W) // 8)
        r_outer = max(4, min(H, W) // 2 - 1)

        y_idx, x_idx = np.indices((H, W))
        dists = np.sqrt((x_idx - cx)**2 + (y_idx - cy)**2)
        mesh_band = (dists >= r_inner) & (dists <= r_outer)

        total_energy = np.sum(mag_spec) - mag_spec[cy, cx]  # exclude DC
        band_energy = np.sum(mag_spec[mesh_band])

        if total_energy > 1e-4:
            mesh_periodicity = float(np.clip((band_energy / total_energy) * 1.5, 0.0, 1.0))
        else:
            mesh_periodicity = 0.0

        # 3. Boundary Tortuosity (perimeter^2 / (4*pi*area))
        _, thresh = cv2.threshold(patch, 150, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        tortuosity = 1.0
        if contours:
            largest = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest)
            perimeter = cv2.arcLength(largest, True)
            if area > 10:
                tortuosity = float((perimeter**2) / (4 * np.pi * area))
                tortuosity = float(np.clip(tortuosity, 1.0, 15.0))

        # Decision rule for net-like acoustic signature
        is_net = (filament_density > 0.25 and mesh_periodicity > 0.20)

        return FilamentEvidence(
            filament_density=filament_density,
            mesh_periodicity_index=mesh_periodicity,
            boundary_tortuosity=tortuosity,
            is_net_like=is_net
        )
