import os
import pytest
from backend.app.services.mission_streamer import mission_streamer

def test_mission_streamer_catalog_and_selection():
    missions = mission_streamer.get_available_missions()
    assert len(missions) >= 3
    
    # Check default mission
    keys = [m["key"] for m in missions]
    assert "baltic_debris" in keys
    assert "northsea_pipeline" in keys
    assert "umich_thunderbay" in keys

    # Test selecting mission
    ok = mission_streamer.set_active_mission("northsea_pipeline")
    assert ok is True
    assert mission_streamer.active_mission_key == "northsea_pipeline"

    # Test payload retrieval
    payload = mission_streamer.get_current_frame_payload()
    if payload:
        assert payload["event_type"] == "MISSION_PING"
        assert "telemetry" in payload
        assert "qc_report" in payload
        assert "contacts" in payload
        assert "frame_image" in payload

    # Test ping advancement
    idx = mission_streamer.advance_ping()
    assert idx >= 0

    # Reset back to umich_thunderbay
    mission_streamer.set_active_mission("umich_thunderbay")
