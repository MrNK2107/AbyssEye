import os
import cv2
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from ml.discovery.classical_proposal import CandidateProposal

class KnownObjectDetector:
    """
    Supervised Known-Object Detector Interface for SSS imagery.
    Loads real fine-tuned YOLOv8 model (trained on 5 classes: shipwreck, natural_object,
    pipe, cylinder, fishing_gear) and generates candidate proposals with real class confidence.
    """

    CLASSES = ["unknown", "pipeline", "shipwreck", "naval_mine", "revetment_wall", "ghost_net", "natural_object"]

    # Mapping from YOLOv8 trained classes to AbyssEye taxonomy
    YOLO_TO_ABYSSEYE = {
        "shipwreck": "shipwreck",
        "pipe": "pipeline",
        "cylinder": "naval_mine",
        "fishing_gear": "ghost_net",
        "natural_object": "natural_object"
    }

    def __init__(self, confidence_threshold: float = 0.01, weights_path: Optional[str] = None):
        self.confidence_threshold = confidence_threshold
        if weights_path is None:
            weights_path = os.path.join("models", "yolov8_best.pt")
        self.weights_path = weights_path
        self._model = None
        self._load_model()

    def _load_model(self):
        if self.weights_path and os.path.exists(self.weights_path):
            try:
                from ultralytics import YOLO
                self._model = YOLO(self.weights_path)
            except Exception as e:
                print(f"[KnownObjectDetector] Warning: could not load YOLO model: {e}")
                self._model = None

    def predict(self, image: np.ndarray, frame_id: str = "frame") -> List[CandidateProposal]:
        """
        Executes real YOLOv8 inference over sonar image.
        Returns detected candidate proposals with class labels and confidence.
        """
        if image is None or image.size == 0:
            return []

        H, W = image.shape[:2]
        proposals = []

        if self._model is not None:
            try:
                # Format image to 3-channel BGR for Ultralytics
                if image.ndim == 2:
                    img_bgr = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
                elif image.ndim == 3 and image.shape[2] == 1:
                    img_bgr = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
                else:
                    img_bgr = image

                results = self._model.predict(img_bgr, conf=self.confidence_threshold, imgsz=640, verbose=False)
                for r_idx, res in enumerate(results):
                    for b_idx, box in enumerate(res.boxes):
                        cls_id = int(box.cls[0].item())
                        cls_name_raw = res.names.get(cls_id, "unknown")
                        conf = float(box.conf[0].item())

                        mapped_class = self.YOLO_TO_ABYSSEYE.get(cls_name_raw, cls_name_raw)
                        x1, y1, x2, y2 = [int(v.item()) for v in box.xyxy[0]]
                        x1 = max(0, min(W - 1, x1))
                        y1 = max(0, min(H - 1, y1))
                        x2 = max(x1 + 1, min(W, x2))
                        y2 = max(y1 + 1, min(H, y2))
                        w = x2 - x1
                        h = y2 - y1

                        cx = x1 + (w / 2.0)
                        cy = y1 + (h / 2.0)

                        crop = image[y1:y2, x1:x2]
                        mean_int = float(np.mean(crop)) if crop.size > 0 else 128.0
                        peak_int = float(np.max(crop)) if crop.size > 0 else 255.0

                        proposals.append(
                            CandidateProposal(
                                proposal_id=f"{frame_id}_yolo_{r_idx}_{b_idx}",
                                bbox=(x1, y1, w, h),
                                centroid=(cx, cy),
                                confidence=conf,
                                sources=["supervised_yolo"],
                                area_px=w * h,
                                mean_intensity=mean_int,
                                peak_intensity=peak_int,
                                aspect_ratio=round(w / max(1, h), 2),
                                detector_class=mapped_class,
                                detector_conf=conf,
                                anomaly_score=conf
                            )
                        )
            except Exception as e:
                print(f"[KnownObjectDetector] Inference error: {e}")

        return proposals

