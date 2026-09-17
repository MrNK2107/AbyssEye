import numpy as np
import cv2
from typing import Tuple, Optional

class SlantRangeCorrector:
    """Corrects side-scan sonar geometric distortion from slant-range to ground-range."""

    @staticmethod
    def correct_channel(
        channel_image: np.ndarray,
        altitude_m: float,
        max_slant_range_m: float,
        ground_resolution_m: float = 0.05
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Converts a 1-channel (Port or Starboard) slant-range image to ground-range.
        
        Args:
            channel_image: 2D array (H, W) where W represents slant range from nadir outward.
            altitude_m: Altitude of sonar transducer above seafloor in meters.
            max_slant_range_m: Maximum slant range covered by the channel in meters.
            ground_resolution_m: Desired uniform ground resolution in meters/pixel.
            
        Returns:
            ground_image: 2D array resampled to uniform ground range.
            ground_ranges_m: 1D array of ground range coordinates for columns.
        """
        H, W = channel_image.shape
        if altitude_m <= 0.1:
            # Altitude unknown or invalid, return original image with linear range estimation
            ground_ranges = np.linspace(0, max_slant_range_m, W)
            return channel_image.copy(), ground_ranges

        # 1. Compute slant range for each column in original image
        slant_ranges = np.linspace(0, max_slant_range_m, W)

        # 2. Compute maximum ground range
        if max_slant_range_m <= altitude_m:
            return channel_image.copy(), slant_ranges

        max_ground_range_m = np.sqrt(max(0.0, max_slant_range_m**2 - altitude_m**2))
        num_ground_cols = max(10, int(np.ceil(max_ground_range_m / ground_resolution_m)))
        ground_ranges_m = np.linspace(0, max_ground_range_m, num_ground_cols)

        # 3. For each uniform ground range Yg, compute required slant range Rs = sqrt(Yg^2 + Ha^2)
        required_slant_ranges = np.sqrt(ground_ranges_m**2 + altitude_m**2)

        # 4. Map required slant range to source column coordinates in [0, W - 1]
        src_cols = (required_slant_ranges / max_slant_range_m) * (W - 1)
        src_cols = np.clip(src_cols, 0, W - 1).astype(np.float32)

        # 5. Build remap coordinate grid
        map_x = np.tile(src_cols, (H, 1))
        map_y = np.tile(np.arange(H, dtype=np.float32)[:, np.newaxis], (1, num_ground_cols))

        # 6. Bilinear interpolation remap
        ground_image = cv2.remap(
            channel_image,
            map_x,
            map_y,
            interpolation=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REPLICATE
        )

        return ground_image, ground_ranges_m

    @staticmethod
    def correct_dual_channel(
        full_waterfall: np.ndarray,
        altitude_m: float,
        max_slant_range_m: float,
        ground_resolution_m: float = 0.05
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Splits dual-channel waterfall (Port on left, Starboard on right) at center nadir,
        corrects both channels, and stitches them back with nadir gap removed.
        """
        H, W = full_waterfall.shape
        mid = W // 2

        port_raw = np.fliplr(full_waterfall[:, :mid])  # Flips so column 0 is nadir
        starboard_raw = full_waterfall[:, mid:]       # Column 0 is nadir

        port_ground, port_ranges = SlantRangeCorrector.correct_channel(
            port_raw, altitude_m, max_slant_range_m, ground_resolution_m
        )
        star_ground, star_ranges = SlantRangeCorrector.correct_channel(
            starboard_raw, altitude_m, max_slant_range_m, ground_resolution_m
        )

        # Stitch: Port flipped back + Starboard
        port_corrected = np.fliplr(port_ground)
        dual_corrected = np.hstack([port_corrected, star_ground])

        return dual_corrected, port_ranges, star_ranges
