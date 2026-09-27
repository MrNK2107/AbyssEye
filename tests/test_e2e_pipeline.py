import pytest
import os
import shutil
import tempfile
import numpy as np

from ml.ingestion.synthetic_generator import SyntheticSonarGenerator
from ml.ingestion.sonar_parser import SonarParser
from backend.app.services.pipeline_orchestrator import PipelineOrchestrator
from ml.active_learning.retrain_service import ActiveLearningRetrainer
from backend.app.services.report_exporter import MissionReportExporter

@pytest.fixture
def multi_ping_survey_dir():
    temp_dir = tempfile.mkdtemp()
    gen = SyntheticSonarGenerator(height_pings=128, width_cols=256, altitude_m=12.0, max_slant_range_m=50.0)
    created_files = gen.generate_survey_dataset(temp_dir, num_frames=5)
    yield temp_dir, created_files
    shutil.rmtree(temp_dir, ignore_errors=True)

def test_full_end_to_end_survey_processing(multi_ping_survey_dir):
    temp_dir, created_files = multi_ping_survey_dir
    orchestrator = PipelineOrchestrator()

    all_contacts = []
    for ping_idx, f_path in enumerate(created_files):
        record = SonarParser.load_from_file(f_path, survey_id="E2E-TEST-SURVEY", ping_index=ping_idx)
        qc, contacts = orchestrator.process_frame(record, ping_index=ping_idx)

        assert qc.status in ["EXCELLENT", "DEGRADED"]
        all_contacts.extend(contacts)

    assert len(all_contacts) >= 1

    # Verify first contact digital twin properties
    sample = all_contacts[0]
    assert "contact_id" in sample
    assert "triage_state" in sample
    assert "spatial_telemetry" in sample
    assert "evidence_graph" in sample
    assert "fusion_decision" in sample

    # Verify calibrated probabilities sum to 1.0
    probs = sample["fusion_decision"]["calibrated_probabilities"]
    assert 0.0 <= probs["p_anthropogenic"] <= 1.0
    assert 0.0 <= probs["p_natural"] <= 1.0
    assert 0.0 <= probs["p_uncertain"] <= 1.0
    total_prob = probs["p_anthropogenic"] + probs["p_natural"] + probs["p_uncertain"]
    assert abs(total_prob - 1.0) < 0.05

    # Verify SHAP feature explanations
    shap_feats = sample["fusion_decision"]["top_shap_features"]
    assert len(shap_feats) > 0

    # Test Mission Report Exporter
    report = MissionReportExporter.generate_json_report("E2E-TEST-SURVEY", all_contacts)
    assert report["survey_id"] == "E2E-TEST-SURVEY"
    assert report["mission_summary"]["total_contacts_surfaced"] == len(all_contacts)

    csv_path = os.path.join(temp_dir, "test_report.csv")
    MissionReportExporter.export_csv(all_contacts, csv_path)
    assert os.path.exists(csv_path)

def test_active_learning_retraining():
    retrainer = ActiveLearningRetrainer()
    retrain_res = retrainer.retrain_model()
    assert retrain_res["status"] == "RETRAINED_SUCCESS"
    assert "brier_score" in retrain_res
    assert os.path.exists(retrain_res["model_path"])
