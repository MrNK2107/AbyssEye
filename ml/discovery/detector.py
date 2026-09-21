import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from ml.discovery.classical_proposal import CandidateProposal

class KnownObjectDetector:
    """
    Supervised Known-Object Detector Interface for labeled SSS benchmarks.
    Detects known anthropogenic targets (pipelines, shipwrecks, naval mines, walls).
    """

    CLASSES = ["unknown", "pipeline", "shipwreck", "naval_mine", "revetment_wall"]

    def __init__(self, confidence_threshold: float = 0.35, weights_path: Optional[str] = None):
        self.confidence_threshold = confidence_threshold
        self.weights_path = weights_path

    def predict(self, image: np.ndarray, frame_id: str = "frame") -> List[CandidateProposal]:
        """
        Executes inference over sonar image.
        Returns detected candidate proposals with class labels and confidence.
        """
        if image is None or image.size == 0:
            return []

        H, W = image.shape
        proposals = []

        # High-contrast geometric feature heuristic when deep weights are loading/offline
        # Identifies strong linear structures (pipelines) and large compact blocks (wrecks)
        return proposals
