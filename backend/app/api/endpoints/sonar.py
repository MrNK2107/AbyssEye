from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
import shutil
import cv2
import time
import asyncio
import numpy as np

from backend.app.core.config import settings
from backend.app.services.pipeline_orchestrator import PipelineOrchestrator
from ml.ingestion.sonar_parser import SonarParser
from ml.ingestion.synthetic_generator import SyntheticSonarGenerator
from backend.app.api.endpoints.contacts import CONTACTS_STORE
from backend.app.api.endpoints.ws import manager

router = APIRouter()
orchestrator = PipelineOrchestrator()

class ProcessSurveyRequest(BaseModel):
    survey_id: str
    file_path: str
    altitude_m: Optional[float] = 12.0
    slant_range_m: Optional[float] = 50.0

class GenerateSurveyRequest(BaseModel):
    survey_id: Optional[str] = "SRV-BALTIC-ACOUSTIC-01"
    num_pings: Optional[int] = 5
    seabed_type: Optional[str] = "sand_ripples" # 'sand_ripples', 'rocky_reef', 'mud_flat'
    target_type: Optional[str] = "ghost_net" # 'ghost_net', 'pipeline', 'shipwreck', 'ordnance'

@router.post("/upload")
async def upload_sonar_file(
    file: UploadFile = File(...),
    survey_id: str = Form("SRV-UPLOAD-01")
):
    upload_dir = os.path.join(settings.UPLOAD_DIR, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    saved_path = os.path.join(upload_dir, file.filename)

    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "status": "UPLOADED",
        "survey_id": survey_id,
        "filename": file.filename,
        "file_path": saved_path
    }

@router.post("/process")
def process_survey_file(req: ProcessSurveyRequest):
    if not os.path.exists(req.file_path):
        raise HTTPException(status_code=404, detail="Sonar file not found")

    record = SonarParser.load_from_file(
        image_path=req.file_path,
        survey_id=req.survey_id,
        altitude_m=req.altitude_m,
        slant_range_m=req.slant_range_m
    )

    qc_report, contacts = orchestrator.process_frame(record, ping_index=0)

    # Cache contacts in store
    for c in contacts:
        CONTACTS_STORE[c["contact_id"]] = c

    return {
        "status": "COMPLETED",
        "survey_id": req.survey_id,
        "qc_report": qc_report.to_dict(),
        "contacts_count": len(contacts),
        "contacts": contacts
    }

@router.post("/generate-and-process")
async def generate_and_process_survey(req: GenerateSurveyRequest):
    """
    Generates a full physics-accurate SSS survey dataset and processes it
    ping-by-ping, broadcasting live telemetry and surfaced contacts via WebSockets.
    """
    survey_id = req.survey_id or f"SRV-LIVE-{int(time.time())}"
    survey_dir = os.path.join("data", "processed", survey_id)
    os.makedirs(survey_dir, exist_ok=True)

    gen = SyntheticSonarGenerator(
        height_pings=384,
        width_cols=768,
        altitude_m=12.0,
        max_slant_range_m=50.0
    )

    created_contacts = []
    all_qc_reports = []

    # Base vessel starting coordinate (Baltic Sea survey track)
    base_lat = 54.8210
    base_lon = 18.7340
    heading = 184.5

    for p_idx in range(req.num_pings or 5):
        t0 = time.time()
        
        # 1. Generate seabed
        canvas = gen.generate_seabed_background(seabed_type=req.seabed_type or "sand_ripples", seed=42 + p_idx)
        
        # 2. Insert target on selected pings
        target_h = 1.6
        c_col = int(gen.width * 0.72) if p_idx % 2 == 0 else int(gen.width * 0.28)
        canvas_with_target, _ = gen.insert_target(
            canvas,
            target_type=req.target_type or "ghost_net",
            center_ping=gen.height // 2,
            center_col=c_col,
            target_height_m=target_h
        )

        file_path = os.path.join(survey_dir, f"ping_{p_idx:04d}.png")
        cv2.imwrite(file_path, canvas_with_target)

        # Advance simulated vessel GPS position along trackline
        cur_lat = base_lat - (p_idx * 0.00035)
        cur_lon = base_lon + (p_idx * 0.00008)

        record = SonarParser.load_from_file(
            image_path=file_path,
            survey_id=survey_id,
            ping_index=p_idx,
            altitude_m=gen.altitude_m,
            slant_range_m=gen.max_slant_range_m,
            heading_deg=heading,
            latitude=cur_lat,
            longitude=cur_lon
        )

        qc_report, contacts = orchestrator.process_frame(record, ping_index=p_idx)
        elapsed_ms = (time.time() - t0) * 1000

        # Cache newly surfaced contacts
        for c in contacts:
            CONTACTS_STORE[c["contact_id"]] = c
            created_contacts.append(c)

        all_qc_reports.append(qc_report.to_dict())

        # Broadcast live ping telemetry over WebSocket
        await manager.broadcast_json({
            "event_type": "PING_PROCESSED",
            "survey_id": survey_id,
            "ping_index": p_idx,
            "total_pings": req.num_pings or 5,
            "qc_status": qc_report.status,
            "snr_db": qc_report.snr_db,
            "contacts_found_in_ping": len(contacts),
            "total_contacts_so_far": len(CONTACTS_STORE),
            "processing_time_ms": round(elapsed_ms, 1),
            "vessel_telemetry": {
                "latitude": round(cur_lat, 6),
                "longitude": round(cur_lon, 6),
                "heading_deg": heading,
                "altitude_m": gen.altitude_m,
                "slant_range_m": gen.max_slant_range_m
            },
            "new_contacts": contacts
        })

        # Small async pause for realistic stream visualization
        await asyncio.sleep(0.15)

    return {
        "status": "COMPLETED",
        "survey_id": survey_id,
        "pings_processed": req.num_pings or 5,
        "contacts_surfaced": len(created_contacts),
        "total_store_contacts": len(CONTACTS_STORE),
        "contacts": created_contacts,
        "qc_reports": all_qc_reports
    }
