import numpy as np
import cv2
import json
import os
from typing import Dict, List, Any, Tuple, Optional

class SyntheticSonarGenerator:
    """
    Procedural Physics-Accurate Side-Scan Sonar Simulator.
    Generates realistic SSS waterfalls with seafloor morphometry, acoustic ray-traced shadows,
    ghost net mesh filaments, pipelines, wrecks, and natural seabed structures.
    """

    def __init__(
        self,
        height_pings: int = 512,
        width_cols: int = 1024,
        altitude_m: float = 12.0,
        max_slant_range_m: float = 50.0,
        frequency_khz: float = 900.0,
        pixel_res_m: float = 0.05
    ):
        self.height = height_pings
        self.width = width_cols
        self.altitude_m = altitude_m
        self.max_slant_range_m = max_slant_range_m
        self.frequency_khz = frequency_khz
        self.pixel_res_m = pixel_res_m
        self.nadir_col = self.width // 2

    def generate_seabed_background(self, seabed_type: str = "sand_ripples", seed: int = 42) -> np.ndarray:
        """Generates background acoustic backscatter with realistic texture and speckle."""
        np.random.seed(seed)
        H, W = self.height, self.width

        # Base mean backscatter intensity
        base_canvas = np.full((H, W), 110.0, dtype=np.float32)

        if seabed_type == "sand_ripples":
            y_indices, x_indices = np.indices((H, W))
            spatial_freq = 0.04
            angle = np.pi / 6.0
            ripple_pattern = np.sin(spatial_freq * (np.cos(angle) * x_indices + np.sin(angle) * y_indices))
            base_canvas += 28.0 * ripple_pattern

        elif seabed_type == "rocky_reef":
            h_sub, w_sub = max(4, H // 8), max(4, W // 8)
            noise1 = cv2.resize(np.random.randn(h_sub, w_sub).astype(np.float32), (W, H))
            noise2 = cv2.resize(np.random.randn(max(4, H // 4), max(4, W // 4)).astype(np.float32), (W, H))
            base_canvas += 35.0 * (0.7 * noise1 + 0.3 * noise2)

        elif seabed_type == "mud_flat":
            base_canvas *= 0.85

        # Add Rayleigh-distributed speckle noise
        rayleigh_speckle = np.random.rayleigh(scale=1.0, size=(H, W)).astype(np.float32)
        sonar_image = base_canvas * (0.8 + 0.2 * rayleigh_speckle)

        # Nadir water column darkening
        nadir_half_width = int((self.altitude_m / self.max_slant_range_m) * (self.width / 2.0))
        if nadir_half_width > 0:
            left_nadir = max(0, self.nadir_col - nadir_half_width)
            right_nadir = min(W, self.nadir_col + nadir_half_width)
            sonar_image[:, left_nadir:right_nadir] *= 0.15

        return np.clip(sonar_image, 0.0, 255.0).astype(np.uint8)

    def insert_target(
        self,
        canvas: np.ndarray,
        target_type: str = "ghost_net",
        center_ping: int = None,
        center_col: int = None,
        target_height_m: float = 1.5,
        target_width_px: int = 24,
        target_length_px: int = 32
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Inserts an anthropogenic or natural target with ray-traced acoustic shadow and highlight physics.
        """
        H, W = canvas.shape
        img = canvas.astype(np.float32).copy()

        if center_ping is None:
            center_ping = H // 2
        if center_col is None:
            center_col = int(W * 0.7)

        center_ping = int(np.clip(center_ping, 10, H - 10))
        center_col = int(np.clip(center_col, 10, W - 10))

        # Determine beam direction (away from nadir)
        is_starboard = (center_col >= self.nadir_col)

        # Calculate slant range from nadir
        dist_from_nadir_px = abs(center_col - self.nadir_col)
        slant_range_m = (dist_from_nadir_px / max(1.0, W / 2.0)) * self.max_slant_range_m
        slant_range_m = max(self.altitude_m + 1.0, slant_range_m)

        # Ray-traced shadow length: Ls = (ht * Rs) / (Ha - ht)
        if self.altitude_m > target_height_m:
            shadow_length_m = (target_height_m * slant_range_m) / (self.altitude_m - target_height_m)
        else:
            shadow_length_m = target_height_m * 4.0

        shadow_length_px = int(np.clip(shadow_length_m / self.pixel_res_m, 8, W // 3))

        x0 = int(np.clip(center_col - target_width_px // 2, 0, W - 1))
        x1 = int(np.clip(center_col + target_width_px // 2, x0 + 1, W))
        y0 = int(np.clip(center_ping - target_length_px // 2, 0, H - 1))
        y1 = int(np.clip(center_ping + target_length_px // 2, y0 + 1, H))

        pw = x1 - x0
        ph = y1 - y0

        # 1. Draw Target Highlight
        if target_type == "ghost_net":
            mesh_patch = np.zeros((ph, pw), dtype=np.float32)
            for py in range(ph):
                for px in range(pw):
                    striation = np.sin(0.8 * px) * np.cos(0.8 * py)
                    if striation > 0.2:
                        mesh_patch[py, px] = 235.0 + np.random.uniform(-15, 15)
                    else:
                        mesh_patch[py, px] = 170.0 + np.random.uniform(-20, 20)
            img[y0:y1, x0:x1] = np.maximum(img[y0:y1, x0:x1], mesh_patch)

        elif target_type == "pipeline":
            cv2.line(img, (x0, y0), (x1, y1), color=245.0, thickness=max(2, target_width_px // 3))

        elif target_type == "shipwreck":
            cv2.rectangle(img, (x0, y0), (x1, y1), color=240.0, thickness=-1)

        else:  # naval_mine or boulder
            cv2.ellipse(img, (center_col, center_ping), (max(2, pw // 2), max(2, ph // 2)), 0, 0, 360, color=240.0, thickness=-1)

        # 2. Draw Acoustic Shadow (Strictly cast outward along the sonar beam vector)
        if is_starboard:
            shadow_x0 = x1
            shadow_x1 = min(W, x1 + shadow_length_px)
        else:
            shadow_x1 = x0
            shadow_x0 = max(0, x0 - shadow_length_px)

        if shadow_x1 > shadow_x0:
            shadow_y0 = max(0, y0 - 2)
            shadow_y1 = min(H, y1 + 2)
            shadow_patch = img[shadow_y0:shadow_y1, shadow_x0:shadow_x1]
            dark_shadow = np.random.uniform(5.0, 18.0, size=shadow_patch.shape).astype(np.float32)
            img[shadow_y0:shadow_y1, shadow_x0:shadow_x1] = dark_shadow

        final_image = np.clip(img, 0.0, 255.0).astype(np.uint8)

        metadata = {
            "target_type": target_type,
            "center_ping": center_ping,
            "center_col": center_col,
            "target_height_m": target_height_m,
            "shadow_length_m": shadow_length_m,
            "slant_range_m": slant_range_m,
            "collinearity_deg": 0.0,
            "channel": "STARBOARD" if is_starboard else "PORT",
            "bbox": [int(x0), int(y0), int(x1 - x0), int(y1 - y0)]
        }

        return final_image, metadata

    def generate_survey_dataset(self, output_dir: str, num_frames: int = 10) -> List[str]:
        """Generates a reproducible suite of synthetic SSS frames with ground-truth sidecar metadata."""
        os.makedirs(output_dir, exist_ok=True)
        created_paths = []

        targets = [
            ("ghost_net", 1.8, "sand_ripples"),
            ("pipeline", 1.2, "mud_flat"),
            ("shipwreck", 4.5, "sand_ripples"),
            ("ghost_net", 2.2, "rocky_reef"),
            ("naval_mine", 0.9, "sand_ripples"),
            ("natural_boulder", 1.4, "rocky_reef"),
            ("none", 0.0, "sand_ripples"),
            ("ghost_net", 1.5, "mud_flat"),
            ("pipeline", 1.0, "sand_ripples"),
            ("none", 0.0, "rocky_reef")
        ]

        for i in range(num_frames):
            t_type, t_height, seabed = targets[i % len(targets)]
            canvas = self.generate_seabed_background(seabed_type=seabed, seed=100 + i)

            targets_meta = []
            if t_type != "none":
                center_c = int(self.width * 0.72) if (i % 2 == 0) else int(self.width * 0.28)
                center_p = int(self.height * 0.5) + (i * 8) % max(1, self.height // 4)
                canvas, meta = self.insert_target(
                    canvas,
                    target_type=t_type,
                    center_ping=center_p,
                    center_col=center_c,
                    target_height_m=t_height
                )
                targets_meta.append(meta)

            frame_id = f"sim_survey_ping_{i:04d}"
            img_path = os.path.join(output_dir, f"{frame_id}.png")
            json_path = os.path.join(output_dir, f"{frame_id}.json")

            cv2.imwrite(img_path, canvas)

            frame_meta = {
                "frame_id": frame_id,
                "survey_id": "SIM-BALTIC-DEMO",
                "ping_index": i,
                "altitude_m": self.altitude_m,
                "slant_range_m": self.max_slant_range_m,
                "heading_deg": 180.0,
                "latitude": 54.821000 + (i * 0.0001),
                "longitude": 18.734000 + (i * 0.00005),
                "channel": "DUAL",
                "pixel_resolution_m": self.pixel_res_m,
                "real": False,
                "synthetic": True,
                "source_dataset": "ABYSSEYE-SIM-V3",
                "ground_truth_targets": targets_meta
            }

            with open(json_path, 'w') as f:
                json.dump(frame_meta, f, indent=2)

            created_paths.append(img_path)

        return created_paths
