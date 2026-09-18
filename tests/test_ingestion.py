import pytest
import numpy as np
import os
import shutil
import tempfile

from ml.ingestion.sonar_parser import SonarParser, SonarFrameRecord
from ml.ingestion.quality_control import QualityControlEngine, QCReport
from ml.preprocessing.slant_range import SlantRangeCorrector
from ml.preprocessing.filters import SonarFilterEngine
from ml.ingestion.synthetic_generator import SyntheticSonarGenerator

@pytest.fixture
def temp_survey_dir():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

def test_synthetic_generator_and_parser(temp_survey_dir):
    gen = SyntheticSonarGenerator(height_pings=128, width_cols=256, altitude_m=10.0, max_slant_range_m=40.0)
    created_files = gen.generate_survey_dataset(temp_survey_dir, num_frames=3)
    assert len(created_files) == 3

    # Test parser on first generated frame
    record = SonarParser.load_from_file(created_files[0])
    assert isinstance(record, SonarFrameRecord)
    assert record.height == 128
    assert record.width == 256
    assert record.altitude_m == 10.0
    assert record.provenance["synthetic"] is True

def test_quality_control_engine():
    qc = QualityControlEngine(max_saturation_pct=5.0, min_snr_db=8.0)

    # 1. Normal image
    normal_img = np.random.uniform(40, 180, (128, 128)).astype(np.uint8)
    report = qc.evaluate(normal_img, altitude_m=12.0)
    assert report.status in ["EXCELLENT", "DEGRADED"]
    assert report.bottom_lock_valid is True

    # 2. Saturated image
    sat_img = np.full((128, 128), 255, dtype=np.uint8)
    report_sat = qc.evaluate(sat_img, altitude_m=12.0)
    assert report_sat.status == "CORRUPTED"
    assert report_sat.saturation_pct == 100.0

def test_slant_range_correction():
    H, W = 100, 200
    test_channel = np.random.uniform(50, 200, (H, W)).astype(np.uint8)

    ground_img, ranges = SlantRangeCorrector.correct_channel(
        channel_image=test_channel,
        altitude_m=10.0,
        max_slant_range_m=50.0,
        ground_resolution_m=0.1
    )
    assert ground_img.shape[0] == H
    assert len(ranges) > 0
    assert ranges[-1] <= 50.0

def test_filters():
    img = np.random.uniform(20, 220, (64, 64)).astype(np.uint8)
    norm = SonarFilterEngine.normalize_intensity(img)
    assert norm.dtype == np.uint8
    assert np.min(norm) >= 0 and np.max(norm) <= 255

    lee = SonarFilterEngine.lee_filter(norm)
    assert lee.shape == img.shape
