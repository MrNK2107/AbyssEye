import pytest
import numpy as np

from ml.tracking.kalman_tracker import MultiPingKalmanTracker, ContactTrack
from ml.discovery.classical_proposal import CandidateProposal

def test_multi_ping_tracking_persistence():
    tracker = MultiPingKalmanTracker(max_dist_gating_px=50.0, confirm_hits_threshold=3, window_size=8)

    # Simulate 5 consecutive pings with slight sensor motion
    for ping in range(5):
        prop = CandidateProposal(
            proposal_id=f"P_{ping}",
            bbox=(100 + ping * 2, 100 + ping * 1, 25, 25),
            centroid=(112.5 + ping * 2, 112.5 + ping * 1),
            confidence=0.88,
            sources=["classical_cv"],
            area_px=625,
            mean_intensity=210.0,
            peak_intensity=245.0,
            aspect_ratio=1.0
        )
        tracks = tracker.update([prop], ping_index=ping)

    assert len(tracks) == 1
    track = tracks[0]
    assert track.status == "CONFIRMED"
    assert track.hits == 5
    assert track.persistence_ratio >= 0.80

def test_transient_noise_pruning():
    tracker = MultiPingKalmanTracker(max_dist_gating_px=50.0, confirm_hits_threshold=3, max_lost_pings=2)

    # Ping 0: transient noise glint
    noise_prop = CandidateProposal(
        proposal_id="NOISE_0",
        bbox=(200, 200, 15, 15),
        centroid=(207.5, 207.5),
        confidence=0.50,
        sources=["classical_cv"],
        area_px=225,
        mean_intensity=180.0,
        peak_intensity=210.0,
        aspect_ratio=1.0
    )
    tracker.update([noise_prop], ping_index=0)
    assert len(tracker.tracks) == 1
    assert tracker.tracks[0].status == "TENTATIVE"

    # Ping 1, 2, 3: no detections at that location
    tracker.update([], ping_index=1)
    tracker.update([], ping_index=2)
    tracker.update([], ping_index=3)

    # Noise track should have been deleted/pruned
    assert len(tracker.tracks) == 0
