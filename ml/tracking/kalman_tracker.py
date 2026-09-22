import numpy as np
from scipy.optimize import linear_sum_assignment
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
from ml.discovery.classical_proposal import CandidateProposal

@dataclass
class TrackObservation:
    ping_index: int
    bbox: Tuple[int, int, int, int]
    centroid: Tuple[float, float]
    confidence: float
    sources: List[str]

@dataclass
class ContactTrack:
    track_id: str
    state: np.ndarray  # [x, y, vx, vy, w, h]
    covariance: np.ndarray  # 6x6
    observations: List[TrackObservation] = field(default_factory=list)
    age_pings: int = 1
    total_window: int = 1
    hits: int = 1
    status: str = "TENTATIVE"  # 'TENTATIVE', 'CONFIRMED', 'LOST', 'DELETED'

    @property
    def persistence_ratio(self) -> float:
        return float(self.hits / max(1, self.total_window))

    @property
    def position_residual_rms(self) -> float:
        if len(self.observations) < 2:
            return 0.1
        residuals = []
        for obs in self.observations:
            dx = obs.centroid[0] - self.state[0]
            dy = obs.centroid[1] - self.state[1]
            residuals.append(np.sqrt(dx**2 + dy**2))
        return float(np.mean(residuals))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "track_id": self.track_id,
            "hits": self.hits,
            "total_window": self.total_window,
            "persistence_ratio": round(self.persistence_ratio, 3),
            "status": self.status,
            "position_residual_rms": round(self.position_residual_rms, 2)
        }


class MultiPingKalmanTracker:
    """
    Kalman Filter Multi-Ping State Tracking & Hungarian Association Engine.
    Tracks side-scan sonar contacts across consecutive pings to confirm temporal persistence.
    """

    def __init__(
        self,
        max_dist_gating_px: float = 60.0,
        confirm_hits_threshold: int = 3,
        max_lost_pings: int = 3,
        window_size: int = 8
    ):
        self.max_dist_gating_px = max_dist_gating_px
        self.confirm_hits_threshold = confirm_hits_threshold
        self.max_lost_pings = max_lost_pings
        self.window_size = window_size
        self.tracks: List[ContactTrack] = []
        self.next_track_id: int = 1

        # Kalman Matrices
        # State: [x, y, vx, vy, w, h]
        self.dt = 1.0
        self.F = np.array([
            [1, 0, self.dt, 0, 0, 0],
            [0, 1, 0, self.dt, 0, 0],
            [0, 0, 1, 0, 0, 0],
            [0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 1]
        ], dtype=np.float32)

        self.H = np.array([
            [1, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0],
            [0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 1]
        ], dtype=np.float32)

        self.Q = np.eye(6, dtype=np.float32) * 1.5   # Process noise
        self.R = np.eye(4, dtype=np.float32) * 4.0   # Measurement noise

    def update(self, proposals: List[CandidateProposal], ping_index: int) -> List[ContactTrack]:
        # 1. Predict state for all active tracks
        for track in self.tracks:
            track.state = self.F @ track.state
            track.covariance = self.F @ track.covariance @ self.F.T + self.Q
            track.age_pings += 1
            track.total_window = min(self.window_size, track.total_window + 1)

        # 2. Hungarian Data Association
        if len(self.tracks) == 0:
            # Initialize tracks for all current proposals
            for p in proposals:
                self._init_track(p, ping_index)
            return self.tracks

        if len(proposals) == 0:
            self._prune_lost_tracks()
            return self.tracks

        cost_matrix = np.zeros((len(self.tracks), len(proposals)), dtype=np.float32)
        for i, track in enumerate(self.tracks):
            tx, ty = track.state[0], track.state[1]
            for j, prop in enumerate(proposals):
                px, py = prop.centroid[0], prop.centroid[1]
                dist = np.sqrt((tx - px)**2 + (ty - py)**2)
                cost_matrix[i, j] = dist

        row_ind, col_ind = linear_sum_assignment(cost_matrix)

        matched_tracks = set()
        matched_proposals = set()

        for r, c in zip(row_ind, col_ind):
            if cost_matrix[r, c] <= self.max_dist_gating_px:
                # Valid match: update Kalman filter
                self._update_kalman(self.tracks[r], proposals[c], ping_index)
                matched_tracks.add(r)
                matched_proposals.add(c)

        # 3. Unmatched proposals become new tentative tracks
        for j, prop in enumerate(proposals):
            if j not in matched_proposals:
                self._init_track(prop, ping_index)

        # 4. Prune stale / lost tracks
        self._prune_lost_tracks()

        return self.tracks

    def _init_track(self, prop: CandidateProposal, ping_index: int):
        x, y, w, h = prop.bbox
        cx, cy = prop.centroid
        state = np.array([cx, cy, 0.0, 0.0, float(w), float(h)], dtype=np.float32)
        cov = np.eye(6, dtype=np.float32) * 10.0

        track = ContactTrack(
            track_id=f"TRK-{self.next_track_id:04d}",
            state=state,
            covariance=cov,
            observations=[TrackObservation(ping_index, prop.bbox, prop.centroid, prop.confidence, prop.sources)],
            age_pings=1,
            total_window=1,
            hits=1,
            status="TENTATIVE"
        )
        self.next_track_id += 1
        self.tracks.append(track)

    def _update_kalman(self, track: ContactTrack, prop: CandidateProposal, ping_index: int):
        x, y, w, h = prop.bbox
        cx, cy = prop.centroid
        z = np.array([cx, cy, float(w), float(h)], dtype=np.float32)

        # Innovation
        y_innov = z - (self.H @ track.state)
        S = self.H @ track.covariance @ self.H.T + self.R
        K = track.covariance @ self.H.T @ np.linalg.inv(S)

        # Update state and covariance
        track.state = track.state + (K @ y_innov)
        I_KH = np.eye(6, dtype=np.float32) - (K @ self.H)
        track.covariance = I_KH @ track.covariance

        track.hits += 1
        track.observations.append(TrackObservation(ping_index, prop.bbox, prop.centroid, prop.confidence, prop.sources))

        if track.hits >= self.confirm_hits_threshold:
            track.status = "CONFIRMED"

    def _prune_lost_tracks(self):
        surviving = []
        for track in self.tracks:
            last_observed_ago = track.age_pings - len(track.observations)
            if last_observed_ago <= self.max_lost_pings:
                surviving.append(track)
            else:
                track.status = "DELETED"
        self.tracks = surviving
