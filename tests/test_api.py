import pytest
from fastapi.testclient import TestClient
import os
import shutil
import tempfile
import numpy as np

from backend.main import app
from ml.ingestion.synthetic_generator import SyntheticSonarGenerator

client = TestClient(app)

@pytest.fixture
def sample_survey_file():
    temp_dir = tempfile.mkdtemp()
    gen = SyntheticSonarGenerator(height_pings=128, width_cols=256)
    paths = gen.generate_survey_dataset(temp_dir, num_frames=1)
    yield paths[0]
    shutil.rmtree(temp_dir, ignore_errors=True)

def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "HEALTHY"
    assert data["version"] == "3.0.0"

def test_process_survey_and_contacts_flow(sample_survey_file):
    # 1. Process synthetic survey file
    process_req = {
        "survey_id": "TEST-SRV-01",
        "file_path": sample_survey_file,
        "altitude_m": 10.0,
        "slant_range_m": 40.0
    }
    res = client.post("/api/v1/sonar/process", json=process_req)
    assert res.status_code == 200
    p_data = res.json()
    assert p_data["status"] == "COMPLETED"
    assert "contacts" in p_data
    assert p_data["contacts_count"] >= 1

    contact = p_data["contacts"][0]
    contact_id = contact["contact_id"]

    # 2. Query contact by ID
    get_res = client.get(f"/api/v1/contacts/{contact_id}")
    assert get_res.status_code == 200
    c_data = get_res.json()
    assert c_data["contact_id"] == contact_id
    assert "evidence_graph" in c_data
    assert "fusion_decision" in c_data

    # 3. Submit Active Learning Review
    review_req = {
        "reviewer_id": "NAV-OFFICER-42",
        "decision": "ANTHROPOGENIC",
        "target_subtype": "GHOST_NET",
        "confidence_rating": 5,
        "flagged_for_cleanup": True,
        "notes": "Verified mesh striations and beam-aligned shadow."
    }
    rev_res = client.post(f"/api/v1/contacts/{contact_id}/review", json=review_req)
    assert rev_res.status_code == 200
    rev_data = rev_res.json()
    assert rev_data["status"] == "SUCCESS"

    # 4. Test GIS GeoJSON endpoints
    gis_res = client.get("/api/v1/gis/contacts")
    assert gis_res.status_code == 200
    gis_data = gis_res.json()
    assert gis_data["type"] == "FeatureCollection"

    tracks_res = client.get("/api/v1/gis/tracks")
    assert tracks_res.status_code == 200
    tracks_data = tracks_res.json()
    assert tracks_data["type"] == "FeatureCollection"
